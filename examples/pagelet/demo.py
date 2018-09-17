from __future__ import print_function

import flask
import os

import pudgy

app = flask.Flask(__name__)
pudgy.register_blueprint(app)

from .demo_components import DemoPage, DemoComponent

@app.route("/")
def hello():
    async_component = DemoComponent()
    async_component.context.update(
        title="first async_component",
        about="this async_component is async and is rendered at the end of the request"
    )
    async_component.set_delay(2)
    async_component.async()

    component = DemoComponent()
    # this component takes one second to prepare and will
    # delay the whole pageload
    component.set_delay(0)
    component.context.update(
        title="second component",
        about="this component arrives first and is rendered in the main page request"
    )

    dp = DemoPage(
        template="example.html",
        component=component,
        async_component=async_component
    )
    dp.call("SetComponent", async_component)

    return dp.pipeline()



if __name__ == "__main__":
    app.run()
