import flask

import components
from components import Component, FlaskPage, BackboneComponent, MustacheComponent, SassComponent
import os

app = flask.Flask(__name__)
components.install(app)


# we set the path for our component library to be in public/ in the app's root dir
Component.set_base_dir(os.path.join(app.root_path, "public"))

class DemoComponent(MustacheComponent, BackboneComponent, SassComponent):
    pass

class DemoPage(FlaskPage):
    pass

@app.route("/")
def hello():
    component = DemoComponent()
    component.context.update(
        title="foobar",
        about="about this component"
    )

    return DemoPage(
        template="example.html",
        component=component
    ).render()



app.run()
