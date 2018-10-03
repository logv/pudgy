
var util = require("common/util");
var Backbone = require("backbone");

window.$ = window.jQuery || window.$;

window.$C = function(name, options, cb) {
  var id = _.uniqueId('sf_');
  activate_component(id, name, options, function(cls) {
    render_component(id, cls, options, cb);
  });
}

var EventEmitter = $require("EventEmitter");
window.SF = new EventEmitter();

function render_component(id, cls, context, cb) {
  // template rendering
  var template_options = _.extend({
      id: id,
      set_default: function(key, value) {
        if (typeof this[key] === "undefined") {
          this[key] = value;
        }
      }
    }, context);

  if (cls.defaults) {
    template_options = _.defaults(
      template_options, cls.defaults);
  }




  var cmp = new cls.superClass(context);
  if (cls.template) {
    var rendered = cls.template(template_options);
    cmp.$el.html(rendered);

    if (!cmp.$el.hasClass("scoped_" + cls._name)) { cmp.$el.addClass("scoped_" + cls._name); }
    if (!cmp.$el.hasClass(cls._name)) { cmp.$el.addClass(cls._name); }
  }


  if (!context.skip_client_init) {
    if (_.isFunction(cmp.client)) { cmp.client(context); }
  }

  cb && cb(cmp);

  return cmp;

}

function activate_component(id, name, context, cb) {
  var instantiate_component = function(m) {
    // class exports
    var cls = m.exports;
    if (!cls.superClass) {
      cls._name = name;
      var events = $P._raw_import(m.events, name + "/events");
      m.events_js = events;
      _.extend(m.exports, events);

      if (m.template) {
        cls.template = _.template(m.template);
      }

      util.inject_css("scoped_" + name, m.css);
      cls.superClass = Backbone.View.extend(m.exports);
    }

    cb && cb(cls);
  }

  $P._load(name, instantiate_component);
}

module.exports = {
  activate_superfluous_component: function(id, name, context, display_immediately, ref) {
    activate_component(id, name, context, function(cls) {
      util.activate_component(id, name, cls, context, ref, function() {
        return render_component(id, cls, context);
      });
    })
  }
}
