from .components import *
from . import proxy

import flask
import dotmap

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
            return cls.js_transform(f.read())

    @classmethod
    def js_transform(cls, js):
        return js

    @classmethod
    def find_file(cls, fname, basedir):
        cls_dir = cls.BASE_DIR

        fname = fname.strip("'\"")
        if fname[0] == ".":
            jsp = "%s.js" % os.path.join(cls_dir, basedir, fname)
        else:
            jsp = "%s.js" % (os.path.join(cls_dir, fname))

        return jsp

    @classmethod
    def render_requires(cls, requested):
        cls_dir = cls.BASE_DIR
        from .components import REQUIRE_RE
        def render_requires_for_js(js, basedir):
            requires = REQUIRE_RE.findall(js)
            ret = {}
            for p in requires:
                p = p.strip("'\"")
                jsp = cls.find_file(p, basedir)

                if os.path.exists(jsp):
                    with open(jsp) as f:
                        js = f.read()
                        js = cls.js_transform(js)
                        ret[p] = js
                else:
                    print("MISSING REQUIRE FILE", jsp, cls.__name__)
                    ret[p] = 'console.log("MISSING REQUIRE FILE %s FROM %s");' % (p, cls.__name__)
                    continue

                ret.update(render_requires_for_js(js, os.path.dirname(jsp)))

            return ret

        def render_requires(component, basedir):
            ret = {}

            requires = set(component.get_requires()).intersection(set(requested))

            for p in requires:
                jsp = cls.find_file(p, basedir)
                if jsp:
                    with open(jsp, "r") as f:
                        js = cls.js_transform(f.read())
                        ret[p] = js

                    ret.update(render_requires_for_js(js, os.path.dirname(jsp)))



            return ret

        return render_requires(cls, cls.__name__)

    def __init__(self, *args, **kwargs):
        self.client = dotmap.DotMap()
        super(JSComponent, self).__init__(*args, **kwargs)

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

# A Big Package will automatically include its requires into a
# package definition
class BigPackage(JSComponent):
    @classmethod
    def get_defines(cls):
        reqs = cls.get_requires()
        return cls.render_requires(reqs)

mark_virtual(
    MustacheComponent,
    JSComponent,
    SassComponent,
    CSSComponent,
    JinjaComponent,
    BigPackage,
)
