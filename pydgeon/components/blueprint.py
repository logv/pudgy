import jinja2
import flask
from flask import Blueprint, render_template, abort

simple_component = Blueprint('components', __name__,
                        template_folder='templates', url_prefix='/components',static_folder='static')

import prelude
import util
import components

import os

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

@simple_component.route('/<component>/requires')
def get_requires(component):

    requested = flask.request.args.getlist('requires[]')

    found = get_component_by_name(component)
    componentName = found.__name__
    base_dir = found.BASE_DIR
    def render_requires_for_js(js, basedir):
        requires = components.REQUIRE_RE.findall(js)
        ret = {}
        for p in requires:
            p = p.strip("'\"")
            if p[0] == ".":
                jsp = "%s.js" % os.path.join(base_dir, basedir, p)
            else:
                jsp = "%s.js" % (os.path.join(base_dir, p))

            if os.path.exists(jsp):
                with open(jsp) as f:
                    js = f.read()
                    ret[p] = js
            else:
                print "MISSING REQUIRE FILE", jsp, component
                ret[p] = 'console.log("MISSING REQUIRE FILE %s FROM %s");' % (p, component)
                continue

            ret.update(render_requires_for_js(js, os.path.dirname(jsp)))

        return ret

    def render_requires(component, basedir):
        ret = {}

        requires = set(component.get_requires()).intersection(set(requested))

        for p in requires:
            p = p.strip("'\"")
            if p[0] == ".":
                jsp = "%s.js" % os.path.join(base_dir, basedir, p)
            else:
                jsp = "%s.js" % (os.path.join(base_dir, p))
            with open(jsp) as f:
                js = f.read()
                ret[p] = js

            ret.update(render_requires_for_js(js, os.path.dirname(jsp)))



        return flask.jsonify(ret)

    # TODO: scoped component css
    if found:
        return render_requires(found, found.__name__)

    abort(404)

@simple_component.route('/<component>')
def show(component):
    found = get_component_by_name(component)

    def render_package(component):
        ret = {}
        t = component.get_template()
        c = component.get_css()
        j = component.get_js()
        r = component.get_requires()

        if t:
            ret["template"] = t

        if c:
            ret["css"] = c

        if j:
            ret["js"] = j

        if r:
            ret["requires"] = r

        return flask.jsonify(ret)

    # TODO: scoped component css
    if found:
        return render_package(found)

    abort(404)

def add_components():
    flask.request.components = []

def render_components():
    import components
    # when lc.__html__ is called, __marshal__ is invoked, so we use lc.render()
    # instead
    lc = components.ComponentLoader()
    lc.context.components = flask.request.components
    html = lc.render()
    return jinja2.Markup(render_template("inject_components.html", html=html))

def render_component(name, **kwargs):
    found = get_component_by_name(name)

    return found(**kwargs)

def install(app):
    app.register_blueprint(simple_component)
    app.before_request(add_components)
    app.jinja_env.globals.update(render_components=render_components)
    app.jinja_env.globals.update(CC=render_component)
