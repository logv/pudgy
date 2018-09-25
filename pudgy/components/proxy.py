import flask

from .components import Component

STR_CLASS = [str]
try:
    STR_CLASS.append(unicode)
except:
    pass
class Proxy(object):
    def __init__(self, *args, **kwargs):
        pass

class HTMLProxy(Proxy):
    def __init__(self, id, *args, **kwargs):
        self.id = id
        self.__html__ = []
        self.type = "_H"
        super(HTMLProxy, self).__init__(*args, **kwargs)

    def __json__(self):
        return { self.type : self.__html_id__() }

    # jquery is limited to only this component's descendants
    def run_jquery(self, fn, strval, selector=None):
        self.__html__.append((fn, strval, selector));
        return self

    def html(self, val, selector=""):
        self.run_jquery("html", val, selector)

    def replace_html(self, val, selector=""):
        self.run_jquery("replaceWith", val, selector)

    def append_html(self, val, selector=""):
        self.run_jquery("append", val, selector)

    def marshal(self):
        flask.request.pudgy.components.add(self)

    def __ajax_object__(self):
        r = {}
        r["html"] = self.get_html_directives()
        return r

    def set_type(self, t):
        self.type = t

    def get_html_directives(self):
        ret = self.__html__
        self.__html__ = []
        return ret

    def __html_id__(self):
        return self.id

class ComponentProxy(HTMLProxy):
    def __init__(self, id, cls, *args, **kwargs):
        super(ComponentProxy, self).__init__(id, cls, *args, **kwargs)

        self.id = id

        if type(cls) in STR_CLASS:
            self.component = cls
        elif isinstance(cls, Component) or issubclass(cls, Component):
            self.component = cls.__name__
        else:
            raise Exception("UNKNOWN COMPONENT TO PROXY FOR", cls)

        self.__calls__ = []
        self.__transfer__ = []

    def marshal(self):
        flask.request.pudgy.components.add(self)

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

    def __ajax_object__(self):
        r = {}
        r["calls"] = self.get_calls()
        r["html"] = self.get_html_directives()
        r["activations"] = self.get_activations()
        return r

    def get_html_directives(self):
        ret = self.__html__
        self.__html__ = []
        return ret


