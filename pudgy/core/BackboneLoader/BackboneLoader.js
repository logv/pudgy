var backbone = require("vendor/backbone");
var util = require("common/util");

module.exports = {
  activate_backbone_component:  function activate_backbone_component(id, name, context, display_immediately, ref) {
    debug("ACTIVATING COMPONENT", id, name);
    context.id = id;

    // Component Bridge is necessary before loading components
    // so they can properly export their functions
    $C(name, function(cls) {
      if (!cls.backboneClass) {
        util.inject_css("scoped_" + name, cls.css);
        cls.backboneClass = Backbone.View.extend(cls.exports);
      }


      util.activate_component(id, name, cls, context, ref, function(ctx) {
        return new cls.backboneClass(ctx);

      });
    });
  }
};
