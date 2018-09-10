from .components import *

from .proxy import Proxy, ComponentProxy, HTMLProxy
from .basic import MustacheComponent, BigPackage, JSComponent, BackboneComponent

class ComponentLoader(CoreComponent, MustacheComponent, BigPackage):
    WRAP_COMPONENT = False

class ReactLoader(CoreComponent, BigPackage):
    WRAP_COMPONENT = False

class ClientBridge(JSComponent):
    def call(self, fn, *args, **kwargs):
        self.__marshal__()

        t = """
            $C("ComponentLoader", function(m) {
                m.exports.call_on_backbone_component("{{id}}", "{{ fn }}", {{ &args }}, {{ &kwargs }});
            });
        """.strip()

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
            elif "_B" in obj and "_C" in obj:
                c = ComponentProxy(obj["_B"], obj["_C"])
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


mark_virtual(
    ClientBridge,
    ServerBridge,
    ComponentLoader,
    Proxy,
    HTMLProxy
)
