var util = require("common/util");
var Backbone = require("backbone");

window.$SF = function(name, options, cb) {
  var id = "myfirstId?";
  console.log("CREATING COMPONENT FROM CLIENT SIDE");
}


module.exports = {

  activate_superfluous_component: function(id, name, context, display_immediately, ref) {
    var instantiate_component = function(m) {
      // class exports
      var cls = m.exports;
      if (!cls.superClass) {
        var events = $P._raw_import(m.events, name + "/events");
        m.events_js = events;
        _.extend(m.exports, events);
        m.template = _.template(m.template);

        util.inject_css("scoped_" + name, m.css);
        cls.superClass = Backbone.View.extend(m.exports);
      }

      // template rendering
      var template_options = _.extend({
          id: id,
          set_default: function(key, value) {
            if (typeof this[key] === "undefined") {
              this[key] = value;
            }
          }
        }, context);

      if (m.exports.defaults) {
        template_options = _.defaults(
          template_options, m.exports.defaults);
      }

      util.activate_component(id, name, cls, context, ref, function(ctx) {
        var rendered = m.template(template_options);


        var cmp = new cls.superClass(ctx);
        cmp.$el.html(rendered);

        return cmp;
      });
    };




    $P._load(name, instantiate_component);

  }

};
