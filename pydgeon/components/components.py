from __future__ import division, print_function


import pystache
import dotmap
import jinja2
import flask
import json
import sass
import os
import re
import hashlib


from .blueprint import simple_component

REQUIRE_RE = re.compile("""require\(['"](.*)['"]\)""")
VIRTUAL_COMPONENTS = set()

from .util import memoize

def dump_values(w):
    if w:
        return w.__json__()

    return None

class Component(object):
    WRAP_COMPONENT = True
    BASE_DIR = simple_component.root_path + "/public/"

    @classmethod
    def set_base_dir(cls, base_dir):
        cls.BASE_DIR = base_dir


    @classmethod
    @memoize
    def get_requires(cls):
        js = cls.get_js()
        requires = REQUIRE_RE.findall(js)
        return requires or []

    @classmethod
    @memoize
    def get_file_for_ext(cls, ext):
        return os.path.join(cls.BASE_DIR, cls.__name__, "%s.%s" % (cls.__name__, ext))

    @classmethod
    @memoize
    def get_css(cls):
        return ""

    @classmethod
    @memoize
    def get_js(cls):
        return ""

    @classmethod
    @memoize
    def get_template(cls):
        return ""

    @classmethod
    @memoize
    def get_version(cls):
        m = hashlib.md5()
        m.update(cls.get_package().data)

        return m.hexdigest()

    @classmethod
    @memoize
    def get_class(cls):
        return cls.__name__


    @classmethod
    @memoize
    def test_package(cls):
        if cls.__name__ in VIRTUAL_COMPONENTS:
            return True

        try:
            pkg = cls.get_package()
        except Exception as e:
            print("ERROR IN PACKAGE", cls.__name__)
            print(e)
            return False

        return True


    @classmethod
    @memoize
    def get_package(cls):
        ret = {}
        t = cls.get_template()
        c = cls.get_css()
        j = cls.get_js()
        r = cls.get_requires()

        if t:
            ret["template"] = t

        if c:
            ret["css"] = c

        if j:
            ret["js"] = j

        if r:
            ret["requires"] = r

        return flask.jsonify(ret)

    def __init__(self, *args, **kwargs):
        self.context = dotmap.DotMap(kwargs)
        self.client = dotmap.DotMap()

        self.__marshalled__ = False

        self.__template_name__ = str(self.__class__.__name__)

        self.__prep__()

    def __prep__(self):
        pass

    def __repr__(self):
        return "%s: %x" % (self.__template_name__, id(self))

    def __html_id__(self):
        hashstr = "%x" % hash(self)

        return "cmp_%s" % hashstr[-7:]

    def __json__(self):
        self.__marshal__()
        return { "_H" : self.__html_id__() }

    def __context__(self):
        return json.dumps(self.client.toDict(), default=dump_values)

    # should we wait for any CSS before revealing the component
    def __display_immediately__(self):
        css = self.get_css()
        if not css:
            return 1

        return 0


    def __activate_tag__(self):
        a = self.__activate__()
        if a:
            return jinja2.Markup('<script type="text/javascript">\n%s\n</script>' % a)

        return ""

    def __activate__(self):
        return ""


    def __html__(self):
        self.__marshal__()
        return self.render()


    def __wrap_div__(self, div):
        if not self.WRAP_COMPONENT:
            return div

        if self.__display_immediately__():
            return "<div id='%s' class='immediate'>%s</div>" % (self.__html_id__(), div)

        return "<div id='%s' style='display: none;'>%s</div>" % (self.__html_id__(), div)


    def __marshal__(self):
        if not self.__marshalled__:
            flask.request.components.add(self)
            self.__marshalled__ = True



    def __render__(self):
        return ""

    def marshal(self, **kwargs):
        self.client.update(**kwargs)
        return self

    def render(self):
        div = self.__render__()
        wrapped = self.__wrap_div__(div)
        return wrapped

class CoreComponent(Component):
    BASE_DIR = simple_component.root_path + "/core/"

class JinjaComponent(Component):
    @classmethod
    @memoize
    def get_template(cls):
        with open(cls.get_file_for_ext("html")) as f:
            return f.read()

    def __render__(self):
        template_str = self.get_template()
        return flask.render_template_string(template_str, **(self.context.toDict()))


class JSComponent(Component):
    @classmethod
    @memoize
    def get_js(cls):
        with open(cls.get_file_for_ext("js")) as f:
            return f.read()

    def __activate__(self):
        t = """activate_component("{{__html_id__}}", "{{ __template_name__ }}", {{ &__context__ }}, {{ __display_immediately__ }} )"""
        rendered =  pystache.render(t, self)
        return jinja2.Markup(rendered)

class CSSComponent(Component):
    @classmethod
    @memoize
    def get_css(cls):
        with open(cls.get_file_for_ext("css")) as f:
            return f.read()

class SassComponent(Component):
    @classmethod
    @memoize
    def get_css(cls):
        css_class = "scope_%s" % (cls.__name__)
        with open(cls.get_file_for_ext("sass")) as f:
            data = f.read()
            return sass.compile(string=".scoped_%s {\n %s\n}" % (cls.__name__, data))


class BackboneComponent(JSComponent):
    def __json__(self):
        self.__marshal__()
        return { "_R" : self.__html_id__() }

    def __activate__(self):
        t = """
            $C("ComponentLoader", function(m) {
                m.exports.activate_backbone_component("{{__html_id__}}", "{{ __template_name__ }}", {{ &__context__ }}, {{ __display_immediately__ }} )
            });
        """.strip()
        rendered =  pystache.render(t, self)
        return jinja2.Markup(rendered)

class MustacheComponent(Component):
    @classmethod
    @memoize
    def get_template(cls):
        with open(cls.get_file_for_ext("mustache")) as f:
            return f.read()

    def __render__(self):
        template_str = self.get_template()
        rendered =  pystache.render(template_str, self.context)
        return self.__wrap_div__(rendered)

class ComponentLoader(CoreComponent, MustacheComponent, JSComponent):
    WRAP_COMPONENT = False

# for a Page to be a proper Component, it needs to give an ID to its body
class Page(Component):
    def __init__(self, *args, **kwargs):
        super(Page, self).__init__(*args, **kwargs)
        self.__marshal__()

    def __activate__(self):
        t = '$("body").attr("id", "%s");' % (self.__html_id__())
        rendered = "%s\n%s" % (t, super(Page, self).__activate__())
        return jinja2.Markup(rendered)

class ClientBridge(BackboneComponent):
    def __init__(self, *args, **kwargs):
        super(ClientBridge, self).__init__(*args, **kwargs)
        self.__calls__ = []

    def call(self, fn, *args, **kwargs):
        self.__calls__.append((fn, args, kwargs))
        self.__marshal__()

    def __activate__(self):
        all = []
        t = """
            $C("ComponentLoader", function(m) {
                m.exports.call_on_backbone_component("{{id}}", "{{ fn }}", {{ &args }}, {{ &kwargs }});
            });
        """.strip()

        for c in self.__calls__:
            fn, args, kwargs = c

            r = pystache.render(t, {
                "fn" : fn,
                "args" : json.dumps(args, default=dump_values),
                "kwargs" : json.dumps(kwargs, default=dump_values),
                "id" : self.__html_id__()
            })

            all.append(r)

        rendered = "%s\n%s" % ("\n".join(all), super(ClientBridge, self).__activate__())
        return jinja2.Markup(rendered)

# A server bridge allows a backbone component to invoke bridge methods on the
# class that inherits from it
class ServerBridge(ClientBridge):
    __remote_calls__ = {}

    @classmethod
    @memoize
    def get_js(cls):
        js = super(ClientBridge, cls).get_js()

        all = ["\n  module.exports.bridge = {}\n"]


        t = """
module.exports.bridge.{{ fn }} = m.exports.add_invocation("{{ cls }}", "{{ fn }}");
            """.strip()
        for c in cls.__remote_calls__:
            all.append(pystache.render(t, {
                "fn" : c,
                "cls" : cls.__name__
            }))

        return """%s\n$C("ComponentLoader", function(m) {\n %s \n })""" % (js, "\n".join(all))

    @classmethod
    def api(cls, fn):
        cls.__remote_calls__[fn.__name__] = fn

    @classmethod
    def invoke(cls, fn, args=[], kwargs={}):
        print("REMOTE INVOKING", cls, fn, args, kwargs)
        return cls.__remote_calls__[fn](*args, **kwargs)


class FlaskPage(Page):
    def render(self):
        kwargs = self.context.toDict()
        r = flask.render_template(self.context.template, **kwargs)
        # notice that we don't call __wrap_div__ on r
        return r


def mark_virtual(*cls):
    for c in cls:
        VIRTUAL_COMPONENTS.add(c.__name__)


mark_virtual(
    MustacheComponent,
    JSComponent,
    ClientBridge,
    ServerBridge,
    BackboneComponent,
    SassComponent,
    CSSComponent,
    JinjaComponent
)
