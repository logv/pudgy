import flask

# we export these components, as well
# TODO: make the mixins take a first param
# that validates the existence of that file to reduce dynamism
from components import Component, BackboneComponent, MustacheComponent, SassComponent

class Page(BackboneComponent):
    pass

class FlaskPage(Page):
    def __init__(self, *args, **kwargs):
        super(Page, self).__init__(*args, **kwargs)
        self.__marshal__()

    def render(self):
        kwargs = self.context.toDict()
        r = flask.render_template(self.context.template, **kwargs)
        r = self.__wrap_div__(r)
        return r

