var LOADED_COMPONENTS = require("common/component_register");
var cmp_events = {};
_.extend(cmp_events, Backbone.Events);

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

function place_refs(d) {
  if (_.isElement(d)) {
    return { "_H" : d.id };
  }

  if (d instanceof Backbone.View) {
    return { "_R" : d.id, "_C": d._type };
  }

  if (_.isObject(d)) {
    _.each(d, function(v, k) {
      d[k] = place_refs(v);

    });
  }

  if (_.isArray(d)) {
    _.each(d, place_refs);
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
      debug("REPLACED _R REF", d._R, LOADED_COMPONENTS[d._R]);
      d = LOADED_COMPONENTS[d._R];
    } else if (d._H) {
      var r = d;
      d = $("#" + r._H);
      if (!d.length) {
        console.log("Can't find HTML element for", r._H,
          "make sure it is placed into the page!");
      }
      debug("REPLACED _H REF", r._H, d);
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
  find_replacement_refs: find_replacement_refs,
  replace_refs: replace_refs,
  place_refs: place_refs,
  inject_css: inject_css,
  wait_for_refs: wait_for_refs,
  cmp_events: cmp_events
}
