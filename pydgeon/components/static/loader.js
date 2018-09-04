(function() {

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
        { requires: _.keys(needed) }, function(res, ok) {
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
    $.get("/components/" + componentName, function(res) {
      debug("REQUIRES ARE", res.requires);
      load_requires(componentName, res.requires, function() {
        debug("INSTANTIATING", componentName, "WITH CONTEXT");
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

  // TODO: render a component from scratch



  function $C(name, cb) {
    load_component(name, cb);
  }

  window.$C = $C;
  var _modules = {};
  window.define = function(name, mod) {
    _modules[name] = mod;
  };

  window.require = function(mod) {
    debug("GETTING REQUIRE", mod);
    return _modules[mod];

  };
})();
