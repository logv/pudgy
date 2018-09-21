(function() {

if (window.$P) {
  return;
}

var _modules = {}; // we need to load these from the prelude, technically
var _defined = {};

var MODULE_PREFIX="var module = {}; var exports = module.exports = {}; (function() {\n";
var MODULE_SUFFIX="\n})(); module.exports";

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


window.define_raw = function(name, mod_code) {
  if (!_defined[name]) {
    _defined[name] = mod_code;
  }
};

window.require = function(mod) {
  if (!_modules[mod]) {
    if (_defined[mod]) {
      _modules[mod] = raw_import(_defined[mod], mod);

      // next time we try to define, we execute the following
      _defined[mod] = "console.log('Trying to redefine " + mod + " ');";
    }
  }


  return _modules[mod];
};

window.$P = {};
$P._modules = _modules;
$P._raw_import = raw_import;
})();
