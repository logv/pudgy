import flask, pudgy
app = flask.Flask(__name__)
pudgy.register_blueprint(app)

# RAPID_PUDGY=1 will auto create the necessary files
class MyComponent(pudgy.BackboneComponent, pudgy.JinjaComponent):
  pass

class MyPage(pudgy.FlaskPage):
  pass


@app.route('/')
def get_index():
  c = MyComponent()

  p = MyPage(template="home.html", c=c)
  return p.render()

app.run(port=2323)
