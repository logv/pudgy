from __future__ import print_function

import flask
import os

import pydgeon

app = flask.Flask(__name__)
pydgeon.register_blueprint(app)

from .demo_components import DemoPage, DemoComponent

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
