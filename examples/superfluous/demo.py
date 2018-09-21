from __future__ import print_function

import flask
import os

import pudgy

app = flask.Flask(__name__)
# component_dir is relative to app.root_path
pudgy.register_blueprint(app, component_dir="demo_components")

from .demo_components import DemoPage, DemoComponent, Button

@app.route("/")
def hello():
    component = Button()
    component.context.update(
        title="a superfluous component",
        name="my first button"
    )

    dp = DemoPage(
        template="example.html",
        component=component,
    )

    dp.call("SetComponent", component)

    return dp.render()


if __name__ == "__main__":
    app.run()
