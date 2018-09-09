from __future__ import print_function

import jinja2
import flask
import json

from flask import Blueprint, render_template, abort

simple_component = Blueprint('components', __name__,
        template_folder='templates', url_prefix='/components',static_folder='static')

from . import prelude, util, components

components.set_base_dir(simple_component.root_path)

import os
import sys

from .util import memoize

# TODO: put a hash on the prelude.js when generating it
@simple_component.route('/prelude.js')
def get_prelude():
    return prelude.make_prelude()

def get_component_by_name(component):
    all_components = util.inheritors(components.Component)
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

        r.update(proxy.get_object())
        r["response"] = ret
    except Exception as e:
        err = str(e)
        r["error"] = err
        print("ERROR INVOKING", component, fn, e)
        import traceback
        traceback.print_exc(file=sys.stdout)

    res[cid] = r

    for p in flask.request.components:
        if isinstance(p, components.bridge.Proxy):
            res[p.id] = p.get_object()

    return flask.jsonify(res)


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

    # TODO: scoped component css
    if found:
        return found.get_package()

    abort(404)

def add_components():
    flask.request.components = set()

def marshal_components(prelude=True):
    from . import components
    # when lc.__html__ is called, __marshal__ is invoked, so we use lc.render()
    # instead
    lc = components.bridge.ComponentLoader()
    lc.context.components = flask.request.components
    flask.request.components = set()
    html = lc.render()

    component_versions = {}
    for c in lc.context.components:
        component_versions[c.get_class()] = "%s" % c.get_version()

    component_versions[lc.get_class()] = lc.get_version()

    postfix = ""
    if flask.request.components:
        postfix = marshal_components(prelude=False)

    return jinja2.Markup(render_template("inject_components.html",
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

@simple_component.after_request
def add_cache_header(response):
    response.cache_control.max_age = 300
    return response

@simple_component.before_app_first_request
def install_pudgy():
    components.validate_components()


    install(flask.current_app)

    # because our first before_request handler never runs, we invoke it
    # manually
    add_components()

def install(app):
    global APP
    APP = app


    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    app.before_request(add_components)
    app.jinja_env.globals.update(marshal_components=marshal_components)
    app.jinja_env.globals.update(CC=render_component)

def register_blueprint(app):
    app.register_blueprint(simple_component)
