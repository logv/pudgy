var util = require("common/util");

var LOADED_COMPONENTS = require("common/component_register");

$C._components = LOADED_COMPONENTS;

var rpc_handler = {
  get: function rpc_handler(target, prop) {
    var fn = target.__bridge[prop];
    if (!fn) {
      throw prop + "is not an RPC function on " +  target.id;
    }

    return _.bind(fn, target);
  }
}

module.exports = {
  add_invocation: function(cls, fn, args, kwargs) {
    var __kwargs__ = {};
    var __cb__ = function() {};
    var __err__ = function(err) {
      console.log("ERROR RUNNING SERVER DIRECTIVE", cls, fn, err);
    };

    function retfn() {

      var that = this;
      var __id__ = this.id;
      var args = _.toArray(arguments);

      _.defer(function() {
        $.ajax($C._url + cls + "/invoke/" + fn,
          {
            type: "POST",
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify({
              args: util.place_refs(args), kwargs: util.place_refs(__kwargs__), cid: __id__
            }),
            success: function(R) {
              _.each(R, function(res, tid) {
                // 1. replace HTML
                _.each(res.html, function(obj) {
                  var fn = obj[0];
                  var v = obj[1];
                  var selector = obj[2];

                  var cmp = $C._components[tid];


                  if (selector) {
                    cmp.$el.find(selector)[fn](v);
                  } else {
                    cmp.$el[fn](v);
                  }
                });

                // 2. activate
                _.each(res.activations, function(a) {
                  raw_import(a, _.uniqueId("act_"));
                });
                // 3. make call
                _.each(res.calls, function(c) {
                  var cls = c[0];
                  var cid = c[1];
                  var fn = c[2];
                  var args = c[3];
                  var kwargs = c[4];

                  try {
                    module.exports.call_on_backbone_component(cid, fn, args, kwargs);
                  } catch(e) {
                    console.error("ERROR", e, "WHILE RUNNING SERVER DIRECTIVE", cls, cid, fn, args, kwargs);
                  }
                });
              });


              _.bind(__cb__, that)(R[__id__].response, R[__id__].error);
            }

        });
      });

      return retfn;
    }

    retfn.done = function(cb) {
      __cb__ = cb;
      return retfn;
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

    util.wait_for_refs(refs, function() {
      util.replace_refs(args);
      util.replace_refs(kwargs);
      var cmp = LOADED_COMPONENTS[id];
      if (_.isFunction(cmp[fn])) {
        var oldkw = cmp[fn].__kwargs__;
        var oldargs = cmp[fn].__args__;

        cmp[fn].__kwargs__ = kwargs;
        cmp[fn].__args__ = args;
        try {
          cmp[fn].apply(cmp, args);
        } finally {
          cmp[fn].__kwargs__ = oldkw;
          cmp[fn].__args__ = oldargs;
        }

      } else {
        console.error("NO SUCH FUNCTION", fn, "IN COMPONENT", id);
      }
    });

  },
  activate_backbone_component:  function activate_backbone_component(id, name, context, display_immediately, ref) {
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
        cmpInst._type = name;

        if (cmpInst.__bridge) {
          // TODO: come back to this and fix RPC to not be a proxy?
          cmpInst.rpc = new Proxy(cmpInst.__bridge, {
            get: function(target, prop) {
              return rpc_handler.get(cmpInst, prop)
            }
          });
        }

        LOADED_COMPONENTS[id] = cmpInst;
        if (ref) {
          console.log("SETTING COMPONENT REF", ref, cmpInst);
          $C._refs[ref] = cmpInst;
        }

        debug("INSTANTIATED COMPONENT", id, name, cmpInst);
        util.inject_css("display_" + id, "\n#" + id + " { display: block !important } \n");
        util.cmp_events.trigger("cmp::" + id);
        if (ref) {
          util.cmp_events.trigger("ref::" + ref);
        }
      });
    });
  }
};
