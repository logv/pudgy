from .components import *
from . import proxy

from .. import util

import flask
import dotmap

from . import assets




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
    JS_LOADER=assets.JSAsset
    EXCLUDE_JS = set()

    @classmethod
    @memoize
    def get_js(cls):
        p = cls.get_file_for_ext(cls.JS_LOADER.EXT)
        loader = cls.get_asset_loader(p)
        with open(p) as f:
            return loader.transform(f.read())

    @classmethod
    def get_asset_loader(cls, filename):
        loaders = util.inheritors(assets.AssetLoader)
        for l in loaders:
            if l.match(filename):
                return l

        return assets.JSAsset


    @classmethod
    def render_requires(cls, requested):
        cls_dir = cls.BASE_DIR
        from .components import REQUIRE_RE
        def render_requires_for_js(js, basedir):
            requires = REQUIRE_RE.findall(js)
            ret = {}
            for p in requires:
                if p in cls.EXCLUDE_JS:
                    continue

                p = p.strip("'\"")
                loader = cls.get_asset_loader(p)
                jsp = loader.find_file(p, basedir, cls.BASE_DIR)
                js = loader.render_file_to_js(jsp)

                if not js:
                    ret[p] = 'console.log("MISSING REQUIRE FILE %s FROM %s");' % (p, cls.__name__)
                    continue

                ret[p] = js
                ret.update(render_requires_for_js(js, os.path.dirname(jsp)))

            return ret

        def render_requires(component, basedir):
            ret = {}

            requires = set(component.get_requires()).intersection(set(requested))

            for p in requires:
                loader = cls.get_asset_loader(p)
                jsp = loader.find_file(p, basedir, cls.BASE_DIR)
                if jsp:
                    js = loader.render_file_to_js(jsp)
                    if js:
                        ret[p] = js
                        ret.update(render_requires_for_js(js, os.path.dirname(jsp)))
                    else:
                        ret[p] = 'console.log("MISSING REQUIRE FILE %s FROM %s");' % (p, cls.__name__)
                        continue



            return ret

        return render_requires(cls, cls.__name__)

    def __init__(self, *args, **kwargs):
        self.__marshalled__ = False
        self.client = dotmap.DotMap()
        super(JSComponent, self).__init__(*args, **kwargs)



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
        t = """$C("ComponentBridge", function(m) {
            m.exports.activate_component("{{__html_id__}}", "{{ __template_name__ }}", {}, {{ &__context__ }}, {{ __display_immediately__ }} )
        })"""
        rendered =  pystache.render(t, self)
        self.__activate_str__ = rendered

    def __marshal__(self):
        if not self.__marshalled__:
            flask.request.pudgy.components.add(self)
            self.__marshalled__ = True

    def marshal(self, **kwargs):
        self.client.update(**kwargs)
        self.__marshal__()
        return self

class CSSComponent(Component):
    CSS_LOADER=assets.CssAsset

    @classmethod
    @memoize
    def load_css(cls):
        p = cls.get_file_for_ext(cls.CSS_LOADER.EXT)
        loader = cls.get_asset_loader(p)
        css_class = "scoped_%s" % (cls.__name__)
        with open(p) as f:
            return loader.transform(f.read(), css_class)

    @classmethod
    @memoize
    def get_css(cls):
        return cls.add_display_rules(cls.load_css())

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
        with open(cls.get_file_for_ext("mustache")) as f:
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
    def get_defines(cls):
        reqs = cls.get_requires()
        return cls.render_requires(reqs)

class BigCSSPackage(Component):
    pass

mark_virtual(
    BigJSPackage,
    BigCSSPackage,
)
