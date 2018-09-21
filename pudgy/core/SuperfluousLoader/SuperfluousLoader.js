var util = require("common/util");
var Backbone = require("backbone");


module.exports = {

  activate_superfluous_component: function(id, name, context, display_immediately, ref) {
    var instantiate_component = function(m) {
      var cls = m.exports;
      if (!cls.superClass) {
        var events = $C._raw_import(m.events, name + "/events");
        m.events_js = events;
        _.extend(m.exports, events);
        m.template = _.template(m.template);

        util.inject_css("scoped_" + name, m.css);
        cls.superClass = Backbone.View.extend(m.exports);
      }



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

      console.log("TEMPLATE OPTIONS", template_options);


      util.activate_component(id, name, cls, context, ref, function(ctx) {
        var rendered = m.template(template_options);


        var cmp = new cls.superClass(ctx);
        cmp.$el.html(rendered);

        console.log("ACTIVATING COMPONENT", cmp, id, name);

        return cmp;
      });
    };




    $C._load(name, instantiate_component);

  }

};
