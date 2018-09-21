var LOADED_COMPONENTS = {};

var _ = require("underscore");
var reqwest = require("reqwest");

window._ = _;
window.reqwest = reqwest;

if (window.$P.set_versions) {
  return;
}

// htmlDecode
function htmlDecode(input){
  var e = document.createElement('div');
  e.innerHTML = input;
  // handle case of empty input
  return e.childNodes.length === 0 ? "" : e.childNodes[0].nodeValue;
}


var DEBUG = false
function debug() {
  if (!DEBUG) {
    return
  }

  console.log(_.toArray(arguments).join(" "));
}

var COMPONENTS = {};
var PENDING = {};


function $get(url, data, cb) {
  reqwest({
    url: url,
    data: data,
    success: cb
  });
}

function load_requires(component, requires, cb) {
  debug("LOADING REQUIRES", requires);
  var needed = {};
  _.each(requires, function(r) {
    if (!_defined[r]) { needed[r] = r; }
  })

  if (_.keys(needed).length > 0) {

    $get($P._url + component + "/requires",
      { requires: _.keys(needed), q: _versions[component] }, function(res, ok) {
      _.each(res, function(v, k) {
        define_raw(k, v);
      });
      cb();
    });
  } else {
    cb();
  }
}



function strip_comment_wrap(str) {
  var chars = str.length;
  chars -= "<!--".length;
  chars -= "-->;".length;

  str = str.replace(/^\s*/, "");
  str = str.replace(/\s*$/, "");

  var ret= str.substr("<!--".length, chars);
  // Decoding from HTML

  return htmlDecode(ret);
}

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

  if (!to_inject) {
    return;
  }

  var stylesheetEl = document.createElement("style");
  stylesheetEl.type = "text/css";

  stylesheetEl.innerHTML = to_inject;
  stylesheetEl.setAttribute('name', name);

  document.head.appendChild(stylesheetEl);
  _injected_css[name] = true;

  return css;
}

_requested_css = {};
function add_component_css(component) {
  if (!component || _injected_css[component] || _requested_css[component]) {
    return
  }
  _requested_css[component] = true;

  $get($P._url + component, { q: _versions[component] }, function(res) {
    inject_css(component, res.css);
  });
}

function inject_pagelet(id) {
  var pagelet_id = "pagelet_" + id;
  // destination is pEl
  var pEl = document.getElementById("pl_" + id);

  // source is sEL
  var sEl = document.getElementById(pagelet_id);

  var payload = strip_comment_wrap(sEl.innerHTML)
  pEl.innerHTML = payload;
}

function load_component(componentName, cb) {
  if (COMPONENTS[componentName]) {
    cb(COMPONENTS[componentName]);
    return;
  }

  if (PENDING[componentName]) {
    PENDING[componentName].push(cb);
    return;
  }

  PENDING[componentName] = [cb];
  $get($P._url + componentName, { q: _versions[componentName] }, function(res) {
    _.each(res.defines, function(v, k) { define_raw(k, v); });

    load_requires(componentName, res.requires, function() {
      var klass = $P._raw_import(res.js, componentName);
      COMPONENTS[componentName] = res;
      res.exports = klass;

      PENDING[componentName].forEach(function(cb) {
        if (cb) {
          cb(res);
        }
      });

    });
  });

}

$P.set_versions = function(versions) {
  _.each(versions, function(v, k) {
    _versions[k] = v;
  });
  debug("VERSIONS", _versions);
};

window.$P = _.extend($P, window.$P || {});
var _versions = {};
$P._load = load_component;
$P._versions = _versions;
$P._refs = {};
$P._raw_import = raw_import;
$P._inject_pagelet = inject_pagelet;
$P._components = LOADED_COMPONENTS;
$P._inject_css= inject_css;
$P._require_css = add_component_css;

