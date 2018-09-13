(function() {
  var LOADED_COMPONENTS = {};

  if (window.$C) {
    return;
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

  var MODULE_PREFIX="var module = {}; var exports = module.exports = {}; (function() {\n";
  var MODULE_SUFFIX="})(); module.exports";

  function raw_import(str, module_name) {
    var toval = "";
    if (module_name) {
      toval = "//# sourceURL=" + module_name + ".js\n";
    }

    toval += MODULE_PREFIX + str + MODULE_SUFFIX;

    var r = eval(toval);

    if (r && r.__esModule) {
      if (r.default) {
        r = r.default;
      }
    }

    return r;
  }

  function load_requires(component, requires, cb) {
    debug("LOADING REQUIRES", requires);
    var needed = {};
    _.each(requires, function(r) {
      if (!_defined[r]) { needed[r] = r; }
    })

    if (_.keys(needed).length > 0) {

      $.get($C._url + component + "/requires",
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
    ret = $('<div />').html(ret).text();

    return ret;
  }

  function inject_pagelet(id) {
    var pagelet_id = "pagelet_" + id;
    // destination is pEl
    var pEl = $("#pl_" + id);

    // source is sEL
    var sEl = $("#" + pagelet_id);

    var payload = strip_comment_wrap(sEl.html());
    pEl.html(payload);
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
    $.get($C._url + componentName, { q: _versions[componentName] }, function(res) {
      _.each(res.defines, function(v, k) { define_raw(k, v); });

      load_requires(componentName, res.requires, function() {
        var klass = raw_import(res.js, componentName);
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

  function $C(name, cb) {
    load_component(name, cb);
  }

  $C.set_versions = function(versions) {
    _.each(versions, function(v, k) {
      _versions[k] = v;
    });
    debug("VERSIONS", _versions);
  }


  window.$C = $C;
  var _modules = {};
  var _versions = {};
  var _defined = {};

  $C._modules = _modules;
  $C._versions = _versions;
  $C._refs = {};
  $C._raw_import = raw_import;
  $C._inject_pagelet = inject_pagelet;
  $C._components = LOADED_COMPONENTS;

  window.define_raw = function(name, mod_code) {
    if (!_defined[name]) {
      _defined[name] = mod_code;
    }
  };

  window.require = function(mod) {
    debug("GETTING REQUIRE", mod);

    if (!_modules[mod]) {
      if (_defined[mod]) {
        _modules[mod] = raw_import(_defined[mod], mod);

        // next time we try to define, we execute the following
        _defined[mod] = "console.log('Trying to redefine " + mod + " ');";
      }
    }


    return _modules[mod];
  };
})();
