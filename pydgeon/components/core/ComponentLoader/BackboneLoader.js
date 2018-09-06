var util = require("common/util");
var LOADED_COMPONENTS = require("common/component_register");

$C._components = LOADED_COMPONENTS;

module.exports = {
  add_invocation: function(cls, fn, args, kwargs) {
    var __kwargs__ = {};
    function retfn() {

      var args = _.toArray(arguments);
      var kwargs = __kwargs__;

      $.ajax($C._url + cls + "/invoke/" + fn,
        {
          type: "POST",
          contentType: "application/json; charset=utf-8",
          data: JSON.stringify({
            args: args, kwargs: kwargs
          }),
          success: function(res) {
            // TODO: this should invoke a cb handed to us, somehow
            console.log("RES", res);
          }
      });

    }

    retfn.kwargs = function(kwargs) {
      __kwargs__ = kwargs;
      return retfn;
    }


    return retfn;
  },
  call_on_backbone_component: function(id, fn, args, kwargs) {
    var refs = { };

    refs[id] = id;
    util.find_replacement_refs(args, refs);
    util.find_replacement_refs(kwargs, refs);

    console.log("UTIL IS", util);
    util.wait_for_refs(refs, function() {
      util.replace_refs(args);
      util.replace_refs(kwargs);
      var cmp = LOADED_COMPONENTS[id];
      if (_.isFunction(cmp[fn])) {
        var oldkw = cmp[fn].__kwargs__;

        cmp[fn].__kwargs__ = kwargs;
        try {
          cmp[fn].apply(cmp, args);
        } finally {
          cmp[fn].__kwargs__ = oldkw;
        }

      } else {
        console.error("NO SUCH FUNCTION", fn, "IN COMPONENT", id);
      }
    });

  },
  activate_backbone_component:  function activate_backbone_component(id, name, context, display_immediately) {
    debug("ACTIVATING COMPONENT", id, name);
    context.id = id;

    var cmpEl = document.getElementById(id);
    $C(name, function(cmp) {
      debug("LOADED COMPONENT PACKAGE", id, name);

      if (!cmp.backboneClass) {
        util.inject_css("scoped_" + name, cmp.css);

        cmp.backboneClass = Backbone.View.extend(cmp.exports);
      }

      context.id = id;
      context.el = cmpEl;
      $(context.el).addClass("scoped_" + name);

      var refs = {};
      util.find_replacement_refs(context, refs);
      util.wait_for_refs(refs, function() {
        util.replace_refs(context);

        var cmpInst = new cmp.backboneClass(context);
        LOADED_COMPONENTS[id] = cmpInst;
        debug("INSTANTIATED COMPONENT", id, name, cmpInst);
        util.inject_css("display_" + id, "\n#" + id + " { display: block !important } \n");
        util.cmp_events.trigger("cmp::" + id);
      });
    });
  }
};
