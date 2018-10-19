from __future__ import print_function

import jinja2
import flask
import json
import dotmap
import base64
import sass

from collections import defaultdict

# 2/3 python
try:
    from StringIO import BytesIO as IO
except ImportError:
    from io import BytesIO as IO

import gzip

from flask import Blueprint, render_template, abort

simple_component = Blueprint('components', __name__,
        template_folder='templates', url_prefix='/components',static_folder='static')

from . import prelude, util, components

components.set_base_dir(simple_component.root_path)

import os
import sys

from .util import memoize, dated_url_for
from .components import Component, CSSComponent


@simple_component.route('/prelude.js')
def get_prelude():
    return prelude.make_prelude()

def get_component_dirs():
    all_components = util.inheritors(Component)
    base_dirs = defaultdict(dict)
    for c in all_components:
        base_dirs[c.get_basehash()][c.NAMESPACE] = c.get_dirhash()

    return json.dumps(base_dirs)

def get_component_by_name(component):
    all_components = util.inheritors(Component)
    found = None
    for c in all_components:
        if c.__name__ == component:
            found = c
            break

    return found

@simple_component.route("/")
def index():
    pass

@simple_component.route('/<component>/invoke/<fn>', methods=['POST'])
def invoke(component, fn):
    found = get_component_by_name(component)

    js = flask.request.get_json()
    cid = js.get("cid", None)
    args = js.get("args", [])
    kwargs = js.get("kwargs", {})

    err = None
    ret = None

    res = {}
    r = {}
    try:
        ret, proxy = found.invoke(cid, fn, args, kwargs)

        r.update(proxy.__ajax_object__())
        r["response"] = ret
    except Exception as e:
        err = str(e)
        r["error"] = err
        print("ERROR INVOKING", component, fn, e)
        import traceback
        traceback.print_exc(file=sys.stdout)

    res[cid] = r

    dirhash = {}
    for p in flask.request.pudgy.components:
        res[p.__html_id__()] = p.__ajax_object__()

    res["__request__"] = {
        "css" : list(flask.request.pudgy.css),
        # activations is raw javascript to run
        "activations" : list(flask.request.pudgy.activations)
    }

    return flask.jsonify(res)


@memoize
def build_css_package(files, components):
    all = []

    for file in files:
        filename = file.strip(".")

        with open(os.path.join(flask.current_app.static_folder, filename)) as f:
            all.append(CSSComponent.CSS_LOADER.transform(f.read()))

    for component in components:
        found = get_component_by_name(component)
        all.append(found.get_css())

    return "\n".join(all)

@simple_component.route('/pkg/<dirhash>')
def get_requires(dirhash):
    d = flask.request.args.get('data[m]')
    requested = json.loads(d)

    base_dir = components.get_basedir(dirhash)
    found = components.get_baseclass(dirhash)

    if found:
        return flask.jsonify(found.render_requires(requested))

    abort(404)

@simple_component.route('/pkg/components')
def get_component_package():
    d = flask.request.args.get("data[m]")
    cs = json.loads(d)

    ret = {}
    for c in cs:
        found = get_component_by_name(c)
        if found:
            ret[c] = found.get_package_object()


    return flask.jsonify(ret)

@simple_component.route('/csspkg')
def get_big_css():
    components = flask.request.args.getlist('components')
    files = flask.request.args.getlist('static')

    if flask.request.args.get('cb64'):
        cb64 = flask.request.args.get('cb64')
        cbs = json.loads(base64.b64decode(cb64))
        components.extend(cbs)


    if flask.request.args.get('fb64'):
        fb64 = flask.request.args.get('fb64')
        fbs = json.loads(base64.b64decode(fb64))
        files.extend(fbs)


    all = build_css_package(files, components)

    r = flask.Response(all)
    r.headers["Content-Type"] = "text/css"
    return r

@simple_component.route('/<component>')
def show(component):
    found = get_component_by_name(component)

    if found:
        return found.get_package()

    abort(404)

def add_components():
    flask.request.pudgy = dotmap.DotMap()
    flask.request.pudgy.components = set()
    flask.request.pudgy.css = set()
    flask.request.pudgy.pagelets = set()
    flask.request.pudgy.activations = []


def marshal_components(prelude=True):
    from . import components
    # when lc.__html__ is called, __marshal__ is invoked, so we use lc.render()
    # instead
    lc = components.bridge.ComponentBridge()
    lc.context.components = flask.request.pudgy.components
    flask.request.pudgy.components = set()
    html = lc.render()

    # TODO: dont send same component version down multiple times
    component_versions = {}
    component_dirhashes = {}
    for c in lc.context.components:
        if c.__marshalled__:
            component_versions[c.get_class()] = "%s" % c.get_version()
            component_dirhashes[c.get_class()] = util.gethash(c.BASE_DIR)
            if c.get_class() in flask.request.pudgy.css:
                flask.request.pudgy.css.remove(c.get_class())

            for d in c.get_class_dependencies():
                component_versions[d.get_class()] = "%s" % d.get_version()
                component_dirhashes[d.get_class()] = util.gethash(d.BASE_DIR)

    component_versions[lc.get_class()] = lc.get_version()

    postfix = ""
    if flask.request.pudgy.components:
        postfix = marshal_components(prelude=False)

    css = flask.request.pudgy.css
    flask.request.pudgy.css = set()

    big_package = []
    big_package.sort(key=lambda w: w.__name__)
    for c in css:
        if type(c) == str:
            big_package.append(c)



    cb64 = base64.b64encode(json.dumps(big_package))

    dirhash_lookup = get_component_dirs()
    activations = flask.request.pudgy.activations

    return jinja2.Markup(render_template("inject_components.html",
        dirhash_lookup=dirhash_lookup, css_package=big_package, activations=activations,
        postfix=postfix, prelude=prelude, html=html, url_for=dated_url_for,
        versions=json.dumps(component_versions)))

def render_component(name, **kwargs):
    found = get_component_by_name(name)

    return found(**kwargs)

def inject_components(response):
    if not flask.request.pudgy.pipelined:
        if response.headers["Content-Type"].find("text/html") == 0:
            if flask.request.pudgy.components:
                injection = marshal_components()
                response.set_data("%s\n%s" % (response.get_data(as_text=True), injection))

    return response

@simple_component.before_app_first_request
def install_pudgy():
    components.validate_components()


    install(flask.current_app)

    # because our first before_request handler never runs, we invoke it
    # manually
    add_components()

# we compress our requests if we can
@simple_component.after_request
def compress_request(response):
    accept_encoding = flask.request.headers.get('Accept-Encoding', '')
    if 'gzip' not in accept_encoding.lower():
        return response

    if (response.status_code < 200 or
        response.status_code >= 300 or
        'Content-Encoding' in response.headers):
        return response

    response.direct_passthrough = False
    if len(response.data) < 2048:
        return response

    gzip_buffer = IO()
    gzip_file = gzip.GzipFile(mode='wb',fileobj=gzip_buffer)
    gzip_file.write(response.data)
    gzip_file.close()

    response.data = gzip_buffer.getvalue()
    response.headers['Content-Encoding'] = 'gzip'
    response.headers['Vary'] = 'Accept-Encoding'
    response.headers['Content-Length'] = len(response.data)

    return response

@simple_component.route('/css/<filename>')
def get_sass(filename):
    filename = os.path.normpath(filename)
    print("FLASK DIR", flask.current_app.static_folder, filename)
    fname = os.path.join(flask.current_app.static_folder, filename)
    print("OPENING FNAME", fname)
    with open(fname) as f:
        return sass.compile(string=f.read())

def add_stylesheet(filename):
    t = "<link rel='stylesheet' href='%s' type='text/css' />" % dated_url_for('components.get_sass', filename=filename)
    return jinja2.Markup(t)

def install(app):
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    app.before_request(add_components)
    app.after_request(inject_components)

    app.jinja_env.globals.update(CC=render_component, add_stylesheet=add_stylesheet)

def register_blueprint(app, component_dir=None):
    app.register_blueprint(simple_component)

    if not component_dir:
        component_dir = "components"

    component_dir = os.path.join(app.root_path, component_dir)


    base_dir = os.path.abspath(component_dir)
    print(" * Pudgy component dir is", base_dir)
    Component.set_base_dir(base_dir)
