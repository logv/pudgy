from __future__ import print_function

import jinja2
import flask
import json
import dotmap

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

from .util import memoize
from .components import Component, CSSComponent


@simple_component.route('/prelude.js')
def get_prelude():
    return prelude.make_prelude()

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

    for p in flask.request.pudgy.components:
        res[p.__html_id__()] = p.__ajax_object__()

    res["__request__"] = {
        "css" : list(flask.request.pudgy.css)
    }

    return flask.jsonify(res)


@simple_component.route('/csspkg')
def get_big_css():
    requested = flask.request.args.getlist('components')
    files = flask.request.args.getlist('static')
    all = []

    for file in files:
        filename = file.strip(".")

        with open(os.path.join(flask.current_app.static_folder, filename)) as f:
            all.append(CSSComponent.CSS_LOADER.transform(f.read()))

    for component in requested:
        found = get_component_by_name(component)
        all.append(found.get_css())



    r = flask.Response("\n".join(all))
    r.headers["Content-Type"] = "text/css"
    return r

    abort(404)

@simple_component.route('/<component>/css')
def get_css(component):
    found = get_component_by_name(component)
    if found:
        r = flask.Response(found.get_css())
        r.headers["Content-Type"] = "text/css"
        return r

    abort(404)

@simple_component.route('/<component>/requires')
def get_requires(component):
    requested = flask.request.args.getlist('requires[]')

    found = get_component_by_name(component)
    if found:
        return flask.jsonify(found.render_requires(requested))

    abort(404)

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
    for c in lc.context.components:
        if c.__marshalled__:
            component_versions[c.get_class()] = "%s" % c.get_version()
            if c.get_class() in flask.request.pudgy.css:
                flask.request.pudgy.css.remove(c.get_class())

            for d in c.get_class_dependencies():
                component_versions[d.get_class()] = "%s" % d.get_version()

    component_versions[lc.get_class()] = lc.get_version()

    postfix = ""
    if flask.request.pudgy.components:
        postfix = marshal_components(prelude=False)

    css = flask.request.pudgy.css
    flask.request.pudgy.css = set()

    big_package = []
    big_package.sort(key=lambda w: w.__name__)
    per_package = []
    for c in css:
        if type(c) == str:
            found = get_component_by_name(c)
            if isinstance(found, components.BigCSSPackage) or \
                    issubclass(found, components.BigCSSPackage):
                big_package.append(c)
            else:
                per_package.append(c)



    return jinja2.Markup(render_template("inject_components.html",
        css_package=big_package, css_singles=per_package,
        postfix=postfix, prelude=prelude, html=html, url_for=dated_url_for,
        versions=json.dumps(component_versions)))

def render_component(name, **kwargs):
    found = get_component_by_name(name)

    return found(**kwargs)

APP=None
def handle_request_to(endpoint, **values):
    url = flask.url_for(endpoint, **values)
    req = flask.Request.from_values(path=url)
    ctx = APP.test_request_context(path=url)

    with ctx:
        res = APP.dispatch_request()
    return res

def dated_url_for(endpoint, **values):
    # we know prelude always returns a string, so
    # we use python string hashing
    if endpoint == 'components.get_prelude':
        res = handle_request_to(endpoint, **values)
        hsh = hash(res)

        values['q'] = "%x" % (hsh)

    # if the endpoint is a filename, we use timestamp hashing
    # (but we should really use content hashing, i guess)
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)

    return flask.url_for(endpoint, **values)

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

def install(app):
    global APP
    APP = app


    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    app.before_request(add_components)
    app.after_request(inject_components)
    app.jinja_env.globals.update(CC=render_component)

def register_blueprint(app, component_dir=None):
    app.register_blueprint(simple_component)

    if not component_dir:
        component_dir = "components"

    component_dir = os.path.join(app.root_path, component_dir)


    base_dir = os.path.abspath(component_dir)
    print(" * Pudgy component dir is", base_dir)
    Component.set_base_dir(base_dir)
