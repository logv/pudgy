from __future__ import print_function

import flask
import os

import pudgy

app = flask.Flask(__name__)
pudgy.register_blueprint(app)
pudgy.preload_components()

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



if __name__ == "__main__":
    app.run()
