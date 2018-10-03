var debug = require("common/debug").make();
var util = require("common/util");
var reqwest = $require("reqwest");

debug.DEBUG = false;

var LOADED_COMPONENTS = require("common/component_register");

module.exports = {
  add_invocation: function(cls, fn, args, kwargs) {
    var __kwargs__ = {};
    var __cb__ = function() {};
    var __bf__ = function() {};
    var __err__ = function(err) {
      console.log("ERROR RUNNING SERVER DIRECTIVE", cls, fn, err);
    };

    function retfn() {

      var that = this;
      var __id__ = this.id;

      var args = _.toArray(arguments);


      _.defer(function() {
        var a = util.place_refs(args);
        var k = util.place_refs(__kwargs__);

        reqwest({
            url: $P._url + cls + "/invoke/" + fn,
            type: "json",
            method: "post",
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify({
              args: a, kwargs: k, cid: __id__
            }),
            success: function(R) {
              _.bind(__bf__, that)(R[__id__].response, R[__id__].error);

              _.each(R, function(res, tid) {
                // 1. replace HTML
                _.each(res.html, function(obj) {
                  var fn = obj[0];
                  var v = obj[1];
                  var selector = obj[2];

                  var cmp = LOADED_COMPONENTS[tid];


                  var $el;
                  if (cmp.$el) { $el = cmp.$el; } else { $el = $("#" + tid) } ;
                  if (selector) {
                    $el.find(selector)[fn](v);
                  } else {
                    $el[fn](v);
                  }
                });
              });

              _.each(R, function(res) {
                _.each(res.css, function(c) {
                  $P._require_css(c);
                });
              });


              _.each(R, function(res, tid) {
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
                    util.call_on_component(cid, fn, args, kwargs);
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

    retfn.ready = function(cb) {
      __bf__ = cb;
      return retfn;
    }

    retfn.before = function(cb) {
      __bf__ = cb;
      return retfn;
    }

    retfn.kwargs = function(kwargs) {
      __kwargs__ = kwargs;
      return retfn;
    }


    return retfn;
  },
  call_on_component: function(id, fn, args, kwargs) {
    util.call_on_component(id, fn, args, kwargs);
  },
  activate_component: function(id, name, context, display_immediately, ref) {
    util.activate_component(id, name, context, display_immediately, ref, function(d) {
      if (!display_immediately) { $P._require_css(name); }
      return d;
    });
  }
};
