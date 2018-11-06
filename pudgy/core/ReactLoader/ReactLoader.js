var util = require("common/util");

// This needs to be over-rideable
var React = require("react");
var ReactDOM = require("react-dom");

$P._modules["vendor/react"] = React;
$P._modules["vendor/react-dom"] = ReactDOM;

// push them into global namespace for whiners like me
window.React = React;
window.ReactDOM = ReactDOM;

module.exports = {
  activate_react_component:  function activate_react_component(id, name, context, display_immediately, ref) {
    el = document.getElementById(id);


    var instantiate_component = function(m) {
      var cls = m.exports;
      if (!m._injected_css) {
        m._injected_css = true;
        util.inject_css("scoped_" + name, m.css);

      }

      util.activate_component(id, name, cls, context, ref, function(ctx) {
        var bridge = cls.__bridge;
        var rEl = React.createElement(cls, ctx);
        var ren = ReactDOM.render(rEl, el);
        ren.id = id;
        ren.__bridge = bridge;
        ren.__react_type = true

        return ren;
      });
    }

    $P._load(name, instantiate_component);

  }

}
