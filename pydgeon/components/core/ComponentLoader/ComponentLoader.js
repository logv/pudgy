var debug = require("common/debug").make();
debug.DEBUG = false;

var cmp_events = {};
_.extend(cmp_events, Backbone.Events);

var LOADED_COMPONENTS = {};

var _injected_css = {};
function inject_css(name, css) {
  if (_injected_css[name]) {
    return css;
  }
  debug("INJECTED CSS FOR", name);

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
  debug("WAITING FOR REFS", refs);

  var after = _.after(_.keys(refs).length, function() {
    debug("REFS LOADED", refs, "MOVING ON");
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
  if (_.isElement(d)) {
    return d;
  }

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
  if (_.isElement(d)) {
    return d;
  }

  if (_.isObject(d)) {
    if (d._R) {
      // replace ref
      debug("REPLACED REF", d._R, LOADED_COMPONENTS[d._R]);
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
  activate_backbone_component:  function activate_backbone_component(id, name, context, display_immediately) {
    debug("ACTIVATING COMPONENT", id, name);
    context.id = id;

    var cmpEl = document.getElementById(id);
    $C(name, function(cmp) {
      debug("LOADED COMPONENT PACKAGE", id, name);

      if (!cmp.backboneClass) {
        inject_css("scoped_" + name, cmp.css);

        cmp.backboneClass = Backbone.View.extend(cmp.exports);
      }

      context.id = id;
      context.el = cmpEl;
      $(context.el).addClass("scoped_" + name);
      debug("SHOWING COMPONENT", name);

      var refs = {};
      find_replacement_refs(context, refs);
      wait_for_refs(refs, function() {
        replace_refs(context);

        var cmpInst = new cmp.backboneClass(context);
        LOADED_COMPONENTS[id] = cmpInst;
        debug("INSTANTIATED COMPONENT", id, name, cmpInst);
        inject_css("display_" + id, "\n#" + id + " { display: block !important } \n");
        cmp_events.trigger("cmp::" + id);
      });
    });
  }
}
