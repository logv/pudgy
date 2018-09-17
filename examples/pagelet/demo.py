from __future__ import print_function

import flask
import os

import pudgy

app = flask.Flask(__name__)
pudgy.register_blueprint(app)

from .demo_components import DemoPage, DemoComponent

@app.route("/")
def hello():
    component = DemoComponent()
    component.context.update(
        title="first component",
        about="about this component"
    )
    component.set_delay(2)

    component.call("handle_click", "SERVER MAIN REQUEST")
    component.async()

    component2 = DemoComponent()
    # this component takes one second to prepare and will
    # delay the whole pageload
    component2.set_delay(1)
    component2.context.update(
        title="second component",
        about="about this component"
    )

    dp = DemoPage(
        template="example.html",
        component=component,
        component2=component2
    ).marshal(
        foobar="baz"
    )

    dp.call("SetComponent", component, filename="foo")

    return dp.pipeline()



if __name__ == "__main__":
    app.run()
