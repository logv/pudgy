(function(){function r(e,n,t){function o(i,f){if(!n[i]){if(!e[i]){var c="function"==typeof require&&require;if(!f&&c)return c(i,!0);if(u)return u(i,!0);var a=new Error("Cannot find module '"+i+"'");throw a.code="MODULE_NOT_FOUND",a}var p=n[i]={exports:{}};e[i][0].call(p.exports,function(r){var n=e[i][1][r];return o(n||r)},p,p.exports,r,e,n,t)}return n[i].exports}for(var u="function"==typeof require&&require,i=0;i<t.length;i++)o(t[i]);return o}return r})()({1:[function(require,module,exports){
var local = require("./local_test");
local.test();

var cmp_events = {};
_.extend(cmp_events, Backbone.Events);

var LOADED_COMPONENTS = {};

var _injected_css = {};
function inject_css(name, css) {
  if (_injected_css[name]) {
    return css;
  }

  var to_inject;
  if (_.isString(css)) {
    to_inject = css;
  }
  if (_.isObject(css)) {
    to_inject = css.code;
  }

  var stylesheetEl = $('<style type="text/css" media="screen"/>');
  stylesheetEl.text(to_inject);
  stylesheetEl.attr("data-name", name);

  $("head").append(stylesheetEl);
  _injected_css[name] = true;

  return css;
}

function wait_for_refs(refs, cb) {
  var needed = 0;

  if (!refs) {
    return cb();
  }
  console.log("WAITING FOR REFS", refs);

  var after = _.after(_.keys(refs).length, function() {
    console.log("REFS LOADED", refs, "MOVING ON");
    cb();
  });

  _.each(refs, function(r, k) {
    if (LOADED_COMPONENTS[r]) {
      after();
    } else {
      cmp_events.once("cmp::" + r, function() {
        after();
      });
    }
  });
}

function find_replacement_refs(d, out) {
  if (_.isObject(d)) {
    if (d._R) {
      out[d._R] = d._R;
    } else {
      _.each(d, function(v, k) { d[k] = find_replacement_refs(v, out); });
    }

  }

  if (_.isArray(d)) {
    _.each(d, function(v) { find_replacement_refs(v, out) });
  }

  return d;
}

// recursively walk down d and replace references
// with their actual components
function replace_refs(d) {
  if (_.isObject(d)) {
    if (d._R) {
      // replace ref
      console.log("REPLACED REF", d._R, LOADED_COMPONENTS[d._R]);
      d = LOADED_COMPONENTS[d._R];
    } else {
      _.each(d, function(v, k) {
        d[k] = replace_refs(v);

      });
    }

  }

  if (_.isArray(d)) {
    _.each(d, replace_refs);
  }

  return d;

}

module.exports = {
  activate_backbone_component:  function activate_backbone_component(id, name, context) {
//    console.log("ACTIVATING COMPONENT", id, name);
    context.id = id;

    $C(name, function(cmp) {
//      console.log("LOADED COMPONENT PACKAGE", id, name);

      var cmpEl = document.getElementById(id);
      if (!cmp.backboneClass) {
        inject_css(name, cmp.css);
        cmp.backboneClass = Backbone.View.extend(cmp.exports);
      }

      context.id = id;
      context.el = cmpEl;
      $(context.el).addClass("scoped_" + name);
      $(context.el).fadeIn();

      var refs = {};
      find_replacement_refs(context, refs);
      wait_for_refs(refs, function() {
        replace_refs(context);

        var cmpInst = new cmp.backboneClass(context);
        LOADED_COMPONENTS[id] = cmpInst;
//        console.log("INSTANTIATED COMPONENT", id, name, cmpInst);
        cmp_events.trigger("cmp::" + id);
      });
    });
  }
}

},{"./local_test":2}],2:[function(require,module,exports){
module.exports = {
  test: function() {
    console.log("TESTING");
  }

};

},{}]},{},[1]);
