from .assets import JSComponent, BigPackage
from .components import CoreComponent, mark_virtual

import pystache

class BackboneLoader(CoreComponent, BigPackage):
    WRAP_COMPONENT = False

class BackboneComponent(JSComponent):
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
            $C("BackboneLoader", function(m) {
                m.exports.activate_backbone_component("{{__html_id__}}", "{{ __template_name__ }}", {{ &__context__ }}, {{ __display_immediately__ }}, "{{ __ref__ }}" )
            });
        """.strip()

        self.__activate_str__ = pystache.render(t, self)

mark_virtual(BackboneLoader, BackboneComponent)
