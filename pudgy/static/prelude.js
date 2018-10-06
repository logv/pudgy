(function() {

if (window.$P) {
  return;
}

var _modules = {}; // we need to load these from the prelude, technically
var _defined = {};

var REQUIRE_STUB = "var require = window._make_require_func('";
var REQUIRE_STUB_END = "'); var $require = _shared_require(require);\n";
var MODULE_PREFIX="var module = {}; var exports = module.exports = {}; (function() {\n";
var MODULE_SUFFIX="\n})(); module.exports";

var namespaced_modules = {};

window._shared_require = function(r) {
  return function(m) {
    if (_modules[m]) {
      return _modules[m];
    }

    return r(m);
  }
}

window._make_require_func = function(base, dirhash) {
  var require = function(mod) {
    if (mod[0] == "." && mod[1] == "/") {
      mod = (base + mod.replace(/^.\//, "/"));
    }

    var om = mod;
    var ns, tokens;

    if (mod.indexOf("::") != -1) {
      tokens = mod.split("::");
      ns = tokens[0];
      mod = tokens[1];
      dirhash = $P._namespaces[require.__basehash][ns] || "UNKNOWN";
    }


    dirhash = dirhash||require.__dirhash||"$";

    mod = (dirhash+ "::" + mod);

    var modules = namespaced_modules[dirhash];
    if (!modules) {
      modules = namespaced_modules[dirhash] = {};
    }

    if (!modules[mod]) {
      if (_defined[mod]) {
        modules[mod] = raw_import(_defined[mod], mod);
      }
    }

    _modules[om] = modules[mod];


    return modules[mod];
  };

  return require;
}

window.require = _make_require_func('');
window.$require = _shared_require(require);


function raw_import(str, module_name) {
  var toval = "";
  if (module_name) {
    toval = "//# sourceURL=" + module_name + ".js\n";
  }

  var tokens = module_name.trim().split("::");
  var ns, name;
  if (tokens.length == 1) {
    ns = "";
    name = tokens[0];
  } else if (tokens.length == 2) {
    ns = tokens[0];
    name = tokens[1];
  }

  var require_stub = REQUIRE_STUB + name.replace("'", "") + "', '" + ns + REQUIRE_STUB_END;

  toval += require_stub + MODULE_PREFIX + str + MODULE_SUFFIX;

  var r = eval(toval);

  if (r && r.__esModule) {
    if (r.default) {
      r = r.default;
    }
  }

  return r;
}


window.define_raw = function(name, mod_code, dirhash) {
  if (dirhash) { name = dirhash + "::" + name; }

  if (!_defined[name]) {
    _defined[name] = mod_code;
  }
};

// https://stackoverflow.com/questions/5898656/test-if-an-element-contains-a-class
function hasClass(element, className) {
    return (' ' + element.className + ' ').indexOf(' ' + className+ ' ') > -1;
}

window.$P = {};
$P._defined = _defined;
$P._modules = _modules;
$P._namespaced_modules = namespaced_modules;
$P._raw_import = raw_import;
$P._addClass = function(cmpEl, name) {
  if (!name) { return; }
  if (!hasClass(cmpEl, name)) {
    cmpEl.className += " " + name + " ";
  }
};

})();
