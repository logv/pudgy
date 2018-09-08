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
    def get_defines(cls):
        pass

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
            return

        try:
            pkg = cls.get_package()
        except Exception as e:
            print("ERROR IN PACKAGE", cls.__name__)
            raise e

        return


    @classmethod
    @memoize
    def get_package(cls):
        ret = {}
        t = cls.get_template()
        c = cls.get_css()
        j = cls.get_js()
        r = cls.get_requires()
        d = cls.get_defines()

        if t:
            ret["template"] = t

        if c:
            ret["css"] = c

        if j:
            ret["js"] = j

        if r:
            ret["requires"] = r

        if d:
            ret["defines"] = d

        return flask.jsonify(ret)

    def __init__(self, *args, **kwargs):
        self.context = dotmap.DotMap(kwargs)
        self.__template_name__ = str(self.__class__.__name__)

        self.__hash__ = "%x" % hash(self)



        self.__prep__()

    def __prep__(self):
        pass

    def __repr__(self):
        return "%s: %x" % (self.__template_name__, id(self))

    def __html_id__(self):
        return "cmp_%s" % self.__hash__

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

    def __marshal__(self):
        return self

    def __html__(self):
        self.__marshal__()
        return self.render()


    def __wrap_div__(self, div):
        if not self.WRAP_COMPONENT:
            return div

        if self.__display_immediately__():
            return "<div id='%s' class='immediate'>%s</div>" % (self.__html_id__(), div)

        return "<div id='%s' style='display: none;'>%s</div>" % (self.__html_id__(), div)

    def __render__(self):
        return ""

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

    @classmethod
    def render_requires(cls, requested):
        cls_dir = cls.BASE_DIR
        def render_requires_for_js(js, basedir):
            requires = REQUIRE_RE.findall(js)
            ret = {}
            for p in requires:
                p = p.strip("'\"")
                if p[0] == ".":
                    jsp = "%s.js" % os.path.join(cls_dir, basedir, p)
                else:
                    jsp = "%s.js" % (os.path.join(cls_dir, p))

                if os.path.exists(jsp):
                    with open(jsp) as f:
                        js = f.read()
                        ret[p] = js
                else:
                    print("MISSING REQUIRE FILE", jsp, component)
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
                    jsp = "%s.js" % os.path.join(cls_dir, basedir, p)
                else:
                    jsp = "%s.js" % (os.path.join(cls_dir, p))
                with open(jsp) as f:
                    js = f.read()
                    ret[p] = js

                ret.update(render_requires_for_js(js, os.path.dirname(jsp)))



            return ret

        return render_requires(cls, cls.__name__)

    def __init__(self, *args, **kwargs):
        super(JSComponent, self).__init__(*args, **kwargs)

        self.client = dotmap.DotMap()
        self.__marshalled__ = False


        self.__activate_str__ = ""
        self.__activations__ = []

    def __add_activation__(self, jscode):
        self.__activations__.append(jscode)

    def __activate_tag__(self):
        self.__activate__()

        a = self.__get_activate_script__()
        if a:
            return jinja2.Markup('<script type="text/javascript">\n%s\n</script>' % a)

        return ""

    def __get_activate_script__(self):
        all = [self.__activate_str__]
        all.extend(self.__activations__)

        return "\n".join(all)

    # override this function to provide a custom activation
    def __activate__(self):
        t = """activate_component("{{__html_id__}}", "{{ __template_name__ }}", {{ &__context__ }}, {{ __display_immediately__ }} )"""
        rendered =  pystache.render(t, self)
        self.__activate_str__ = t

    def __marshal__(self):
        if not self.__marshalled__:
            flask.request.components.add(self)
            self.__marshalled__ = True

    def marshal(self, **kwargs):
        self.client.update(**kwargs)
        self.__marshal__()
        return self

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

    def set_ref(self, name):
        # TODO: validate there is only one of each named ref on the page
        self.__ref__ = name
        return self

    def __activate__(self):
        super(BackboneComponent, self).__activate__()

        # we override the activation string with our backbone activation string
        t = """
            $C("ComponentLoader", function(m) {
                m.exports.activate_backbone_component("{{__html_id__}}", "{{ __template_name__ }}", {{ &__context__ }}, {{ __display_immediately__ }}, "{{ __ref__ }}" )
            });
        """.strip()

        self.__activate_str__ = pystache.render(t, self)

class MustacheComponent(Component):
    @classmethod
    @memoize
    def get_template(cls):
        with open(cls.get_file_for_ext("mustache")) as f:
            return f.read()

    def __render__(self):
        template_str = self.get_template()
        rendered =  pystache.render(template_str, self.context)
        return rendered

# for a Page to be a proper Component, it needs to give an ID to its body
class Page(Component):
    def __init__(self, *args, **kwargs):
        super(Page, self).__init__(*args, **kwargs)
        self.__marshal__()

    def __activate__(self):
        super(Page, self).__activate__()

        t = '$("body").attr("id", "%s");' % (self.__html_id__())
        self.__add_activation__(t)

# A Big Package will automatically include its requires into a
# package definition
class BigPackage(JSComponent):
    @classmethod
    def get_defines(cls):
        reqs = cls.get_requires()
        return cls.render_requires(reqs)

class ComponentLoader(CoreComponent, MustacheComponent, BigPackage):
    WRAP_COMPONENT = False

class Proxy(object):
    def __init__(self, *args, **kwargs):
        pass

class HTMLProxy(Proxy):
    def __init__(self, id, *args, **kwargs):
        self.id = id
        self.__html__ = []
        super(HTMLProxy, self).__init__(*args, **kwargs)

    # jquery is limited to only this component's descendants
    def run_jquery(self, fn, strval, selector=None):
        self.__html__.append((fn, strval, selector));
        return self

    def replace_html(self, val, selector=""):
        self.run_jquery("html", val, selector)

    def append_html(self, val, selector=""):
        self.run_jquery("append", val, selector)

    def marshal(self):
        flask.request.components.add(self)

    def get_object(self):
        r = {}
        r["html"] = self.get_html_directives()
        return r

    def get_html_directives(self):
        ret = self.__html__
        self.__html__ = []
        return ret



class ComponentProxy(HTMLProxy):
    def __init__(self, id, cls, *args, **kwargs):
        super(ComponentProxy, self).__init__(id, cls, *args, **kwargs)

        self.id = id

        if type(cls) == str:
            self.component = cls
        elif isinstance(cls, Component) or issubclass(cls, Component):
            self.component = cls.__name__
        else:
            raise Exception("UNKNOWN COMPONENT TO PROXY FOR", cls)

        self.__calls__ = []
        self.__transfer__ = []

    def marshal(self):
        flask.request.components.add(self)

    def call(self, fn, *args, **kwargs):
        self.__calls__.append((fn, args, kwargs))
        return self

    def transfer(self, *args):
        self.__transfer__.extend(args)
        return self

    def get_activations(self):
        ret = []
        for t in self.__transfer__:
            ret.append(t.__get_activate_script__())

        self.__transfer__ = []
        return ret

    def get_calls(self):
        r = [ [self.component, self.id] + list(c) for c in self.__calls__ ]
        self.__calls__ = []
        return r

    def get_object(self):
        r = {}
        r["calls"] = self.get_calls()
        r["html"] = self.get_html_directives()
        r["activations"] = self.get_activations()
        return r

    def get_html_directives(self):
        ret = self.__html__
        self.__html__ = []
        return ret


class ClientBridge(JSComponent):
    def __init__(self, *args, **kwargs):
        super(ClientBridge, self).__init__(*args, **kwargs)
        self.__calls__ = []

    def call(self, fn, *args, **kwargs):
        self.__calls__.append((fn, args, kwargs))
        self.__marshal__()

    def __activate__(self):
        super(ClientBridge, self).__activate__()


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

            self.__add_activation__(r)

# A server bridge allows a backbone component to invoke bridge methods on the
# class that inherits from it
class ServerBridge(ClientBridge):
    __remote_calls__ = {}

    @classmethod
    @memoize
    def get_js(cls):
        js = super(ClientBridge, cls).get_js()

        all = [""" module.exports.__bridge = {}; """]


        t = """
module.exports.__bridge.{{ fn }} = m.exports.add_invocation("{{ cls }}", "{{ fn }}");
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
    def replace_refs(cls, obj, refs=None):
        if refs is None:
            refs = []

        if type(obj) == dict:
            if "_H" in obj:
                h = HTMLProxy(obj["_H"])
                refs.append(h)
                return h

            elif "_R" in obj and "_C" in obj:
                c = ComponentProxy(obj["_R"], obj["_C"])
                refs.append(c)
                return c

            else:
                for k in obj:
                    obj[k] = cls.replace_refs(obj[k], refs)

        if type(obj) == list:
            return [cls.replace_refs(r, refs) for r in obj]


        return obj


    @classmethod
    def invoke(cls, cid, fn, args=[], kwargs={}):
        # we instantiate a proxy for our class instance here,
        # like:
        refs = []
        args = cls.replace_refs(args, refs)
        kwargs = cls.replace_refs(kwargs, refs)

        for r in refs:
            r.marshal()

        c = ComponentProxy(cid, cls)

        args = [c] + args

        return cls.__remote_calls__[fn](*args, **kwargs), c


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
    JinjaComponent,
    BigPackage
)
