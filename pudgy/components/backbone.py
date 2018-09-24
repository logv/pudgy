from .basic import JSComponent, BigJSPackage
from .components import CoreComponent, Virtual

import pystache

class BackboneLoader(CoreComponent, BigJSPackage):
    WRAP_COMPONENT = False

JSComponent.alias_requires("backbone", "vendor/backbone")
@Virtual
class BackboneComponent(JSComponent):
    @classmethod
    def get_class_dependencies(cls):
        return [ BackboneLoader]

    def __json__(self):
        self.__marshal__()
        return { "_B" : self.__html_id__() }

    def set_ref(self, name):
        # TODO: validate there is only one of each named ref on the page
        self.__ref__ = name
        return self

    def __activate__(self):
        super(BackboneComponent, self).__activate__()
        # TODO: BackboneLoader should be referenced via intermediate Class

        # we override the activation string with our backbone activation string
        t = """
            $P._load("BackboneLoader", function(m) {
                m.exports.activate_backbone_component("{{__html_id__}}", "{{ __template_name__ }}", {{ &__context__ }}, {{ __display_immediately__ }}, "{{ __ref__ }}" )
            });
        """.strip()

        self.__activate_str__ = pystache.render(t, self)

