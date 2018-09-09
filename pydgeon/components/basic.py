from .components import *

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

    # TODO: not sure I like having to call super() in activations.
    # they should be different functions, perhaps
    def __activate__(self):
        super(Page, self).__activate__()

        t = '$("body").attr("id", "%s");' % (self.__html_id__())
        self.__add_activation__(t)

class FlaskPage(Page):
    def render(self):
        kwargs = self.context.toDict()
        r = flask.render_template(self.context.template, **kwargs)
        # notice that we don't call __wrap_div__ on r
        return r


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
    BackboneComponent,
    FlaskPage,
    SassComponent,
    CSSComponent,
    JinjaComponent,
    Page,
    BigPackage
)
