var util = require("common/util");
var react = require("vendor/react");
var reactDom = require("vendor/react-dom");

var LOADED_COMPONENTS = require("common/component_register");

module.exports = {
  activate_react_component:  function activate_react_component(id, name, context, display_immediately, ref) {
    el = document.getElementById(id);

    $C(name, function(m) {
        var cls = m.exports;
        if (!m._injected_css) {
          m._injected_css = true;
          util.inject_css("scoped_" + name, m.css);

        }

        util.activate_component(id, name, cls, context, ref, function(ctx) {
          console.log("CTX IS", ctx);
          var rEl = React.createElement(cls, ctx);
          var ren = ReactDOM.render(rEl, el);
          ren.id = id;

          return ren;
        });
    });

  }

}
