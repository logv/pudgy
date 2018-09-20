from .components import Component

import flask
import os

from .bigpipe import Pipeline

from .basic import RAPID_PUDGY_KEY, touch
from .basic import Activatable

# for a Page to be a proper Component, it needs to give an ID to its body
class Page(Activatable, Pipeline):
    def __init__(self, *args, **kwargs):
        super(Page, self).__init__(*args, **kwargs)
        self.__marshalled__ = False

        self.__marshal__()


    def __get_activate_script__(self):
        print "GETTING PAGE ACTIVATION SCRIPT"
        all = [self.__activate_str__]
        all.extend(self.__activations__)

        return "\n".join(all)

    def __activate__(self):
        print "ACTIVATING PAGE", self
        super(Page, self).__activate__()

        t = 'document.body.id = "%s";' % (self.__html_id__())
        self.__add_activation__(t)

        t = 'document.body.className += " scoped_%s ";' % (self.__template_name__)
        self.__add_activation__(t)

class FlaskPage(Page, Pipeline):
    def render(self):
        self.__prepare__()

        flask.request.pudgy.components.add(self)

        kwargs = self.context.toDict()
        if RAPID_PUDGY_KEY in os.environ:
            template_dir = os.path.join(flask.current_app.root_path, flask.current_app.template_folder)
            template_file = os.path.join(template_dir, self.context.template)
            if not os.path.exists(template_file):
                try:
                    os.makedirs(os.path.dirname(template_file))
                except Exception as e:
                    pass

                touch(template_file)
                print(" * Created %s (TURBO_PUDGY)" % template_file)

        r = flask.render_template(self.context.template, **kwargs)
        # notice that we don't call __wrap_div__ on r
        return r
