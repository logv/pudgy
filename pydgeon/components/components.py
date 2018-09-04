import pystache
import dotmap
import jinja2
import flask
import json
import sass
import os
import re


import blueprint
from blueprint import simple_component

REQUIRE_RE = re.compile("""require\(['"](.*)['"]\)""")
class Component(object):
    WRAP_COMPONENT = True
    BASE_DIR = simple_component.root_path + "/public/"

    @classmethod
    def set_base_dir(cls, base_dir):
        cls.BASE_DIR = base_dir

    @classmethod
    def get_requires(cls):
        js = cls.get_js()
        requires = REQUIRE_RE.findall(js)
        return requires or []

    @classmethod
    def get_file_for_ext(cls, ext):
        return os.path.join(cls.BASE_DIR, cls.__name__, "%s.%s" % (cls.__name__, ext))

    @classmethod
    def get_css(cls):
        try:
            with open(cls.get_file_for_ext("css")) as f:
                return f.read()
        except Exception, e:
            return ""

    @classmethod
    def get_js(cls):
        try:
            with open(cls.get_file_for_ext("js")) as f:
                return f.read()
        except Exception, e:
            return ""

    @classmethod
    def get_template(cls):
        try:
            with open(cls.get_file_for_ext("html")) as f:
                return f.read()
        except Exception, e:
            return ""

    def __init__(self, *args, **kwargs):
        self.context = dotmap.DotMap(kwargs)
        self.client = dotmap.DotMap()

        self.__template_name__ = str(self.__class__.__name__)
        self.__render_only__ = False

        self.__prep__()

    def __prep__(self):
        pass

    def __repr__(self):
        return "%s: %x" % (self.__template_name__, id(self))

    def __html_id__(self):
        hashstr = "%x" % hash(self)

        return "cmp_%s" % hashstr[-7:]

    def __json__(self):
        # returns a JSON version of this component
        return { "_R" : self.__html_id__() }

    def __context__(self):
        def dump_values(w):
            if w:
                return w.__json__()

            return None

        return json.dumps(self.client.toDict(), default=dump_values)

    # should we wait for any CSS before revealing the component
    def __display_immediately__(self):
        css = self.get_css()
        if not css:
            return 1

        return 0


    def __activate__(self):
        t = """activate_component("{{__html_id__}}", "{{ __template_name__ }}", {{ &__context__ }}, {{ __display_immediately__ }} )"""
        rendered =  pystache.render(t, self)
        print "ACTIVATE", rendered
        return jinja2.Markup(rendered)


    def __html__(self):
        self.__marshal__()
        return self.render()


    def __wrap_div__(self, div):
        if self.__display_immediately__:
            return "<div id='%s'>%s</div>" % (self.__html_id__(), div)

        return "<div id='%s' style='visibility: hidden;'>%s</div>" % (self.__html_id__(), div)


    def __marshal__(self):
        if self.__render_only__:
            return

        flask.request.components.append(self)

    def __render__(self):
        template_str = self.get_template()
        rendered =  flask.render_template_string(template_str, **(self.context.toDict()))
        if self.__class__.WRAP_COMPONENT:
            return self.__wrap_div__(rendered)
        else:
            return rendered

    def marshal(self, **kwargs):
        self.client.update(**kwargs)
        return self

    def render(self):
        try:
            return self.__render__()
        except Exception, e:
            print e
            raise Exception("NO TEMPLATE TO RENDER", self.__template_name__)

    # if render_only is called, we don't marshall ourself
    def render_only(self):
        self.__render_only__ = True
        return self

class CoreComponent(Component):
    BASE_DIR = simple_component.root_path + "/core/"

class SassComponent(Component):
    @classmethod
    def get_css(cls):
        css_class = "scope_%s" % (cls.__name__)
        try:
            with open(cls.get_file_for_ext("sass")) as f:
                data = f.read()
                return sass.compile(string=".scoped_%s {\n %s\n}" % (cls.__name__, data))
        except Exception, e:
            return ""


class BackboneComponent(Component):
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
    def get_template(cls):
        try:
            with open(cls.get_file_for_ext("mustache")) as f:
                return f.read()
        except Exception, e:
            return ""

    def __render__(self):
        template_str = self.get_template()
        rendered =  pystache.render(template_str, self.context)
        if self.__class__.WRAP_COMPONENT:
            return self.__wrap_div__(rendered)
        else:
            return rendered

class ComponentLoader(CoreComponent, MustacheComponent):
    WRAP_COMPONENT = False

