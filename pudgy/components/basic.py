from __future__ import print_function

from .components import *
from . import proxy

from .. import util

import flask
import dotmap

from . import assets

import os

RAPID_PUDGY_KEY="TURBO_PUDGY"
CREATE_FILES=RAPID_PUDGY_KEY in os.environ
def touch(fname):
    if os.path.exists(fname):
        os.utime(fname, None)
    else:
        open(fname, 'a').close()


def openfile(fname):
    try:
        return open(fname)
    except IOError as e:
        if CREATE_FILES:
            basedir = os.path.dirname(fname)
            try:
                os.makedirs(basedir)
            except:
                pass
            touch(fname)

            print("CREATED FILE FOR COMPONENT:", fname)
            return open(fname)
        else:
            print(" * use %s=1 to auto-create" % RAPID_PUDGY_KEY, fname)
            raise e

class Activatable(object):

    def __init__(self, *args, **kwargs):
        self.__activate_str__ = ""
        self.__activations__ = []
        super(Activatable, self).__init__(*args, **kwargs)

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
        return


class JinjaComponent(Component):
    @classmethod
    @memoize
    def get_template(cls):
        with openfile(cls.get_file_for_ext("html")) as f:
            return f.read()

    def __render__(self):
        template_str = self.get_template()
        return flask.render_template_string(template_str, **(self.context.toDict()))

class JSComponent(Activatable, Component):
    JS_LOADER=assets.JSAsset
    EXCLUDE_JS = set()
    MODULE_MAP = {}
    DEFINITIONS = {}

    @classmethod
    @memoize
    def get_js(cls):
        p = cls.get_file_for_ext(cls.JS_LOADER.EXT)
        loader = cls.get_asset_loader(p)

        dirhash_prefix = "require.__dirhash = '%s'" % cls.get_dirhash()
        basehash_prefix = "require.__basehash = '%s'" % cls.get_basehash()
        with openfile(p) as f:
            l = loader.transform(f.read())

        return "%s\n%s\n%s" % (dirhash_prefix, basehash_prefix, l)

    @classmethod
    def get_asset_loader(cls, filename):
        loaders = util.inheritors(assets.AssetLoader)
        for l in loaders:
            if l.match(filename):
                return l

        return assets.JSAsset

    @classmethod
    def alias_requires(cls, name, fname):
        cls.MODULE_MAP[name] = fname

    @classmethod
    def define_requires(cls, name, filename=None, data=None):
        if filename:
            with openfile(filename) as f:
                data = f.read()


        cls.DEFINITIONS[name] = data


    @classmethod
    @memoize
    def render_requires(cls, requested, check_intersection=False):
        cls_dir = os.path.join(cls.BASE_DIR, cls.NAMESPACE)
        from .components import REQUIRE_RE

        def requires_to_js(p, basedir):
            loader = cls.get_asset_loader(p)
            sp = p
            if sp in cls.DEFINITIONS:
                js = cls.DEFINITIONS[sp]
                jsp = cls_dir
            else:
                if sp in cls.MODULE_MAP:
                    sp = cls.MODULE_MAP[p]

                jsp = loader.find_file(sp, basedir, cls_dir)
                if jsp:
                    js = loader.render_file_to_js(jsp)

            return js, jsp

        def render_requires_for_js(js, basedir):
            requires = REQUIRE_RE.findall(js)
            ret = {}
            for p in requires:
                if p in cls.EXCLUDE_JS:
                    continue

                p = p.strip("'\"")
                js, jsp = requires_to_js(p, basedir)

                if not js:
                    ret[p] = '$P._missing("%s");' % (p)
                    continue

                ret[p] = js
                ret.update(render_requires_for_js(js, os.path.dirname(jsp)))

            return ret

        def render_requires(component, basedir):
            ret = {}

            if check_intersection:
                requires = set(component.get_requires()).intersection(set(requested))
            else:
                requires = set(requested)

            for p in requires:
                js, jsp = requires_to_js(p, basedir)

                if js:
                    ret[p] = js
                    ret.update(render_requires_for_js(js, os.path.dirname(jsp)))
                else:
                    ret[p] = '$P._missing("%s");' % (p)
                    continue



            return ret

        return render_requires(cls, cls.__name__)

    def __init__(self, *args, **kwargs):
        self.__marshalled__ = False
        self.client = dotmap.DotMap()
        super(JSComponent, self).__init__(*args, **kwargs)

    def __marshal__(self):
        if not self.__marshalled__:
            flask.request.pudgy.components.add(self)
            self.__marshalled__ = True

    def __activate__(self):
        t = """$P._load("ComponentBridge", function(m) {
            m.exports.activate_component("{{__html_id__}}", "{{ __template_name__ }}", {{ &__context__ }}, {{ __display_immediately__ }} )
        })"""
        rendered =  pystache.render(t, self)
        self.__activate_str__ = rendered

    def __ajax_object__(self):
        self.__activate__()
        return { "activations" : [self.__get_activate_script__()] }

    def marshal(self, **kwargs):
        self.client.update(**kwargs)
        self.__marshal__()
        return self

    # set a component to not get marshalled to the client. once called, this
    # can't easily be undone.
    def nomarshal(self):
        if self in flask.request.pudgy.components:
            flask.request.pudgy.components.remove(self)
        self.__marshalled__ = True

class CSSComponent(Component):
    CSS_LOADER=assets.CssAsset

    @classmethod
    @memoize
    def load_css(cls):
        p = cls.get_file_for_ext(cls.CSS_LOADER.EXT)
        loader = cls.get_asset_loader(p)
        css_class = "scoped_%s" % (cls.__name__)
        with openfile(p) as f:
            return loader.transform(f.read(), css_class)

    @classmethod
    @memoize
    def get_css(cls):
        return cls.add_display_rules(cls.load_css())


    @classmethod
    def get_asset_loader(cls, filename):
        loaders = util.inheritors(assets.AssetLoader)
        for l in loaders:
            if l.match(filename):
                return l

        return assets.CssAsset

    @classmethod
    def add_display_rules(cls, data):
        return "%s\n .wf_%s, .scoped_%s { display: inherit !important; } " % (data, cls.__name__, cls.__name__)


    def __init__(self, *args, **kwargs):
        super(CSSComponent, self).__init__(self, *args, **kwargs)

        if flask.request:
            if not self.__template_name__ in flask.request.pudgy.css:
                flask.request.pudgy.css.add(self.__template_name__)

class SassComponent(CSSComponent):
    CSS_LOADER=assets.SassAsset

class MustacheComponent(Component):
    @classmethod
    @memoize
    def get_template(cls):
        with openfile(cls.get_file_for_ext("mustache")) as f:
            return f.read()

    def __render__(self):
        template_str = self.get_template()
        rendered =  pystache.render(template_str, self.context)
        return rendered

mark_virtual(
    MustacheComponent,
    JSComponent,
    SassComponent,
    CSSComponent,
    JinjaComponent,
)

# A Big Package will automatically include its requires into a
# package definition
class BigJSPackage(JSComponent):
    @classmethod
    @memoize
    def get_defines(cls):
        reqs = cls.get_requires()
        return cls.render_requires(reqs)

class BigCSSPackage(Component):
    pass

mark_virtual(
    BigJSPackage,
    BigCSSPackage,
)
