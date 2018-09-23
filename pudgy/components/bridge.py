from .components import *

from .proxy import Proxy, ComponentProxy, HTMLProxy
from .basic import MustacheComponent, BigJSPackage, JSComponent

import flask

class ComponentBridge(CoreComponent, MustacheComponent, BigJSPackage):
    WRAP_COMPONENT = False


class ClientBridge(JSComponent):
    def call(self, fn, *args, **kwargs):
        self.__marshal__()

        t = """
            $P._load("ComponentBridge", function(m) {
                m.exports.call_on_component("{{id}}", "{{ fn }}", {{ &args }}, {{ &kwargs }});
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
    def get_class_dependencies(cls):
        return [ ComponentBridge ]
    @classmethod
    @memoize
    def get_rpc_definitions(cls):
        all = [];


        t = """
    ex.__bridge.{{ fn }} = m.exports.add_invocation("{{ cls }}", "{{ fn }}");
            """.strip()

        for c in cls.__remote_calls__:
            all.append(pystache.render(t, {
                "fn" : c,
                "cls" : cls.__name__
            }))

        return """var ex = exports.default || module.exports; ex.__bridge = {};\n$P._load("ComponentBridge", function(m) { \n%s\n}\n);""" % ("\n".join(all))

    @classmethod
    @memoize
    def get_js_supplements(cls):
        return [cls.get_rpc_definitions()]

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
                h.set_type("_H")
                refs.append(h)
                return h

            elif "_R" in obj and "_C" in obj:
                c = ComponentProxy(obj["_R"], obj["_C"])
                c.set_type("_R")
                refs.append(c)
                return c
            elif "_B" in obj and "_C" in obj:
                c = ComponentProxy(obj["_B"], obj["_C"])
                c.set_type("_B")
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
    ComponentBridge,
    Proxy,
    HTMLProxy
)
