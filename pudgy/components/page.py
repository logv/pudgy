from .components import Component

import flask
import os

from .bigpipe import Pipeline

from .basic import RAPID_PUDGY_KEY, touch
from .basic import Activatable

from ..util import dated_url_for

import pystache

# for a Page to be a proper Component, it needs to give an ID to its body
class Page(Activatable, Pipeline):
    def __init__(self, *args, **kwargs):
        super(Page, self).__init__(*args, **kwargs)
        flask.request.pudgy.components.add(self)

        self.__marshalled__ = False

        self.__marshal__()

    def __activate__(self):
        super(Page, self).__activate__()

        # after the fact activations, set the body ID and className at the end
        # of the request. this can lead to flash of unstyled content, so prefer
        #  to use FlaskPage and put the class on the body at the start
        t = 'document.body.id = "%s";' % (self.__html_id__())
        self.__add_activation__(t)

        t = '$P._addClass(document.body, "scoped_%s");' % (self.__template_name__)
        self.__add_activation__(t)

class FlaskPage(Page, Pipeline):
    PAGE_TEMPLATE = """
<html>
<head> {{ &head }} </head>
<body id="{{ id }}" class="{{ class }}" {{ &hidden }}> {{ &body }} </body>
</html>
    """

    def __init__(self, *args, **kwargs):
        super(FlaskPage, self).__init__(*args, **kwargs)
        self.__head__ = []
        self.__stylecomps__ = []
        self.__stylesheets__ = []

    def get_head(self):
        self.render_stylesheets()
        return "\n".join(self.__head__)

    def render_stylesheet_package(self):

        b64_encode_requires = False

        if b64_encode_requires:
            import base64
            import json
            comps = json.dumps(self.__stylecomps__)
            files = json.dumps(self.__stylesheets__)

            comps = base64.b64encode(comps)
            files = base64.b64encode(files)

            url = dated_url_for('components.get_big_css', cb64=comps, fb64=files)
        else:
            url = dated_url_for('components.get_big_css',
                components=self.__stylecomps__,
                static=self.__stylesheets__)

        self.__head__.append("<link rel='stylesheet' href='%s' />" % url)

    def render_single_stylesheets(self):
        for s in self.__stylecomps__:
            url = dated_url_for('components.get_css', component=s)
            self.__head__.append("<link rel='stylesheet' href='%s' />" % url)

        for s in self.__stylesheets__:
            url = dated_url_for('static', filename=s)
            self.__head__.append("<link rel='stylesheet' href='%s' />" % url)


    def render_stylesheets(self):
        if not self.__stylecomps__ and not self.__stylesheets__:
            return [""]

        # self.render_single_stylesheets()
        self.render_stylesheet_package()

        self.__stylecomps__ = []
        self.__stylesheets__ = []

    def add_to_head(self, line):
        self.__head__.append(line)
        return self

    def add_stylesheet(self, name):
        self.__stylesheets__.append(name)
        return ""

    def add_component_stylesheet(self, c):
        self.__stylecomps__.append(c)
        return ""


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

        # techncially, we might render <head> twice, but i think its fine for
        # most browsers - they will treat second <head> as part of the body.
        # TODO: determine what sort of effects this can cause
        kwargs['add_stylesheet'] = self.add_stylesheet
        b = flask.render_template(self.context.template, **kwargs)
        if not self.__display_immediately__():
            self.add_component_stylesheet(self.__template_name__)

        # head after body, because we need everyone to add their styles first
        h = self.get_head()

        inst = {
            "head" : h,
            "body" : b,
            "id" : self.__html_id__(),
            "class" : self.__classname__(),
        }

        # notice that we don't call __wrap_div__ on r, because we are putting our own
        # wrappings in place
        r = pystache.render(self.PAGE_TEMPLATE, inst)
        return r
