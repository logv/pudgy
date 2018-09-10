var debug = require("common/debug").make();
var util = require("common/util");
debug.DEBUG = false;

var LOADED_COMPONENTS = require("common/component_register");

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
        var a = util.place_refs(args);
        var k = util.place_refs(__kwargs__);

        $.ajax($C._url + cls + "/invoke/" + fn,
          {
            type: "POST",
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify({
              args: a, kwargs: k, cid: __id__
            }),
            success: function(R) {
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


    retfn.kwargs = function(kwargs) {
      __kwargs__ = kwargs;
      return retfn;
    }


    return retfn;
  },
  call_on_component: function(id, fn, args, kwargs) {
    util.call_on_component(id, fn, args, kwargs);
  },

};