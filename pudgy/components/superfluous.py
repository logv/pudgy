from .basic import JSComponent, CSSComponent, BigJSPackage, openfile
from .components import CoreComponent, Virtual

import pystache
import flask
import re
import os

from ..util import memoize

JSComponent.alias_requires("backbone", "vendor/backbone")

class SuperfluousLoader(CoreComponent, BigJSPackage):
    WRAP_COMPONENT = False

# https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')
def to_snake_case(name):
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()

@Virtual
class SuperfluousComponent(JSComponent, CSSComponent):
    @classmethod
    def get_file_for_ext(cls, ext):
        cname = to_snake_case(cls.__name__)
        cls_dir = cls.get_dir()
        fname = os.path.join(cls_dir, cname, "%s.%s" % (cname, ext))
        return fname

    @classmethod
    def get_class_dependencies(cls):
        return [ SuperfluousLoader ]

    @classmethod
    def get_template(cls):
        with openfile(cls.get_file_for_ext("html.erb")) as f:
            return f.read()

    @classmethod
    def get_events(cls):
        cname = to_snake_case(cls.__name__)
        cls_dir = cls.get_dir()
        with openfile(os.path.join(cls_dir, cname, "events.js")) as f:
            return f.read()

    @classmethod
    @memoize
    def get_package_object(cls):
        # in a superfluous package, it is:
        # the_component_name.html.erb for template
        # the_component_name.js for js
        # events.js for events
        # the_component_name.css for css
        ret = {}

        j = cls.get_js()
        js_supplements = cls.get_js_supplements()
        if js_supplements:
            js_supplements = "\n".join(js_supplements)

        ret["template"] = cls.get_template()
        ret["css"] = cls.get_css()
        ret["js"] = "%s\n%s" % (j, js_supplements or "")
        ret["requires"] = cls.get_requires()
        ret["defines"] = cls.get_defines()
        ret["events"] = cls.get_events()

        # clean up items
        ret = {k: v for k, v in ret.items() if v}

        return ret


    def __json__(self):
        self.__marshal__()
        return { "_S" : self.__html_id__() }

    def __activate__(self):
        self.client.update(self.context)
        super(SuperfluousComponent, self).__activate__()
        # TODO: SuperfluousLoader should be referenced via intermediate Class

        # we override the activation string with our backbone activation string
        t = """
            $P._load("SuperfluousLoader", function(m) {
                m.exports.activate_superfluous_component("{{__html_id__}}", "{{ __template_name__ }}", {{ &__context__ }}, {{ __display_immediately__ }}, "{{ __ref__ }}" )
            });
        """.strip()

        self.__activate_str__ = pystache.render(t, self)
