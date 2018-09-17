from __future__ import print_function

import flask
import os

import pudgy

app = flask.Flask(__name__)
# component_dir is relative to app.root_path
pudgy.register_blueprint(app, component_dir="demo_components")

from .demo_components import DemoPage, DemoComponent

# over-ride require('react') with our own version
pudgy.JSComponent.define_requires("react",
    filename=os.path.join(app.root_path, 'static/my-react.js'))

@app.route("/")
def hello():
    component = DemoComponent()
    component.context.update(
        title="a react component",
        about=""
    )

    dp = DemoPage(
        template="example.html",
        component=component,
    )

    dp.call("SetComponent", component)

    return dp.render()


if __name__ == "__main__":
    app.run()
