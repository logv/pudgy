(function() {

if (window.$P) {
  return;
}

var _modules = {}; // we need to load these from the prelude, technically
var _defined = {};

var REQUIRE_STUB = "var require = window._make_require_func('";
var REQUIRE_STUB_END = "');\n";
var MODULE_PREFIX="var module = {}; var exports = module.exports = {}; (function() {\n";
var MODULE_SUFFIX="\n})(); module.exports";


window._make_require_func = function(base) {
  var require = function(mod) {

    if (mod[0] == "." && mod[1] == "/") {
      mod = (base + mod.replace(/^.\//, "/"));
      console.log("REQUIRING", mod, _defined);
    }
    if (!_modules[mod]) {
      if (_defined[mod]) {
        _modules[mod] = raw_import(_defined[mod], mod);

        // next time we try to define, we execute the following
        _defined[mod] = "console.log('Trying to redefine " + mod + " ');";
      }
    }


    return _modules[mod];
  };

  return require;
}

window.require = _make_require_func('');

function raw_import(str, module_name) {
  var toval = "";
  if (module_name) {
    toval = "//# sourceURL=" + module_name + ".js\n";
  }

  var require_stub = REQUIRE_STUB + module_name.trim().replace("'", ) + REQUIRE_STUB_END;

  toval += require_stub + MODULE_PREFIX + str + MODULE_SUFFIX;

  var r = eval(toval);

  if (r && r.__esModule) {
    if (r.default) {
      r = r.default;
    }
  }

  return r;
}


window.define_raw = function(name, mod_code) {
  if (!_defined[name]) {
    _defined[name] = mod_code;
  }
};

window.$P = {};
$P._defined = _defined;
$P._modules = _modules;
$P._raw_import = raw_import;
})();
