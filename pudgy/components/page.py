from .components import Component

import flask

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


