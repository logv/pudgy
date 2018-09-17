var util = require("common/util");
var React = require("vendor/react");

$C._modules["react"] = React
var ReactDOM = require("vendor/react-dom");
$C._modules["react-dom"] = ReactDOM;

// push them into global namespace for whiners like me
window.React = React;
window.ReactDOM = ReactDOM;

var LOADED_COMPONENTS = require("common/component_register");

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

        return ren;
      });
    }

    $C(name, instantiate_component);

  }

}
