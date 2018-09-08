from __future__ import print_function

import flask
import os

import pydgeon

app = flask.Flask(__name__)
pydgeon.register_blueprint(app)


class DemoDir(pydgeon.Component):
    BASE_DIR = os.path.join(app.root_path, "demo_components")

class DemoComponent(DemoDir, pydgeon.MustacheComponent, pydgeon.SassComponent,
    pydgeon.BackboneComponent, pydgeon.ClientBridge):
    pass

class DemoPage(DemoDir, pydgeon.ServerBridge, pydgeon.FlaskPage, 
    pydgeon.BackboneComponent):
    pass

@DemoPage.api
def server_call(self, component=None):
    if component:
        component.append_html("<br />ADDED FROM SERVER AJAX CALL")
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
