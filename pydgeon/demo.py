from __future__ import print_function

import flask
import os

from .components import Component, FlaskPage, BackboneComponent, MustacheComponent, \
    SassComponent, ClientBridge, ServerBridge

from .components import install as install_components


app = flask.Flask(__name__)
install_components(app)


# we set the path for our component library to be in public/ in the app's root dir
Component.set_base_dir(os.path.join(app.root_path, "public"))

class DemoComponent(MustacheComponent, SassComponent, BackboneComponent, ClientBridge):
    pass

class DemoPage(ServerBridge, FlaskPage, BackboneComponent):
    pass

@DemoPage.api
def server_call(self, component=None):
#    if component:
#        component.replace_html("SERVER AJAX SET")
    component.call("handle_click", "SERVER AJAX")
    self.call("handle_data", data="some_custom_data")
    return { "some_data": "HANDLING DATA" }

@app.route("/")
def hello():
    component = DemoComponent()
    component.context.update(
        title="foobar",
        about="about this component"
    )

    component.call("handle_click", "SERVER MAIN REQUEST")

    dp = DemoPage(
        template="example.html",
        component=component,
    ).marshal(
        foobar="baz"
    )

    dp.call("SetComponent", component, filename="foo")

    return dp.render()



app.run()
