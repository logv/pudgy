(function() {

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

  var MODULE_PREFIX="var module = {}; (function() {\n";
  var MODULE_SUFFIX="})(); module.exports";

  function raw_import(str, module_name) {
    var toval = "";
    if (module_name) {
      toval = "//# sourceURL=" + module_name + ".js\n";
    }

    toval += MODULE_PREFIX + str + MODULE_SUFFIX;

    return eval(toval);
  }

  function load_requires(component, requires, cb) {
    debug("LOADING REQUIRES", requires);
    var needed = {};
    _.each(requires, function(r) {
      if (!_modules[r]) { needed[r] = r; }
    })

    if (_.keys(needed).length > 0) {

      $.get("/components/" + component + "/requires",
        { requires: _.keys(needed), q: _versions[component] }, function(res, ok) {
        _.each(res, function(v, k) {
          define(k, raw_import(v, k));
        });
        cb();
      });
    } else {
      cb();
    }
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
    $.get("/components/" + componentName, { q: _versions[componentName] }, function(res) {
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
  window.define = function(name, mod) {
    _modules[name] = mod;
  };

  window.require = function(mod) {
    debug("GETTING REQUIRE", mod);
    return _modules[mod];
  };

  window.activate_component = function(id, name, context, display_immediately) { };
})();
