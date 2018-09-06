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

class DemoComponent(MustacheComponent, BackboneComponent, SassComponent):
    pass

class DemoPage(ServerBridge, FlaskPage):
    pass

@DemoPage.api
def server_call(foo):
    return { "data" : "some custom data" }


@app.route("/")
def hello():
    component = DemoComponent()
    component.context.update(
        title="foobar",
        about="about this component"
    )



    dp = DemoPage(
        template="example.html",
        component=component,
    )

    dp.call("SetComponent", component, filename="foo")

    return dp.render()



app.run()
