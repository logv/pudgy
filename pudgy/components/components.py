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


REQUIRE_RE = re.compile("""require\(['"](.*?)['"]\)""")
VIRTUAL_COMPONENTS = set()

from ..util import memoize, getrandhash, inheritors

def dump_values(w):
    if w:
        return w.__json__()

    return None

class Component(object):
    WRAP_COMPONENT = True
    BASE_DIR = None

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

        cleaned =  [r for r in requires if r not in cls.EXCLUDE_JS]
        return cleaned

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
    def get_js_supplements(cls):
        return []

    @classmethod
    @memoize
    def get_template(cls):
        return ""

    @classmethod
    def get_class_dependencies(cls):
        return [ ]

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
        js_supplements = cls.get_js_supplements()
        if js_supplements:
            js_supplements = "\n".join(js_supplements)

        r = cls.get_requires()
        d = cls.get_defines()

        ret["template"] = t
        ret["css"] = c
        ret["js"] = "%s\n%s" % (j, js_supplements or "")
        ret["requires"] = r
        ret["defines"] = d

        # clean up items
        ret = {k: v for k, v in ret.items() if v}

        return flask.jsonify(ret)

    def __init__(self, *args, **kwargs):
        self.context = dotmap.DotMap(kwargs)
        self.__template_name__ = str(self.__class__.__name__)
        self.__async__ = False
        self.__hash__ = getrandhash(self)[:10]



    def __prepare__(self):
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
        jss = self.get_requires()
        if jss:
            for f in jss:
                if f.endswith(".css") or f.endswith(".sass"):
                    return 0

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
            return "<div id='%s' class='immediate scoped_%s'>%s</div>" % (self.__html_id__(), self.__template_name__, div)

        return "<div id='%s' class='scoped_%s' style='display: none;'>%s</div>" % (self.__html_id__(),
            self.__template_name__, div)

    def __render__(self):
        return ""

    def render(self):
        if not self.__async__: # async components get prepared separately
            self.__prepare__()

        div = self.__render__()
        wrapped = self.__wrap_div__(div)
        return wrapped

class CoreComponent(Component):
    pass

def set_base_dir(d):
    Component.set_base_dir(os.path.join(d, "components"))
    CoreComponent.set_base_dir(os.path.join(d, "core"))

@memoize
def validate_components():
    valid = 0
    broken = []
    virtual_components = set()
    for c in inheritors(Component):
        if c.__name__ in VIRTUAL_COMPONENTS:
            virtual_components.add(c.__name__)

        try:
            pkg = c.test_package()
            if not c.__name__ in virtual_components:
                valid += 1
        except Exception as e:
            s = "%s Errors:" % (c.__name__)
            s_ = "-" *  len(s)
            broken.append(c.__name__)
            print(s)
            print(s_)
            print(e)

    print("Validated %s components before first request, %s broken" % (valid + len(broken), len(broken)))
    if broken:
        print("Broken:", ",".join(broken))


def mark_virtual(*cls):
    for c in cls:
        VIRTUAL_COMPONENTS.add(c.__name__)


mark_virtual(
    Component,
    CoreComponent,
)

def Virtual(cls):
    mark_virtual(cls)
    return cls
