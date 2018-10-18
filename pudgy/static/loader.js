var _ = $require("underscore");
var reqwest = $require("reqwest");
var EventEmitter = $require("EventEmitter");


window._ = _;
window.reqwest = reqwest;

var LOADED_COMPONENTS = {};
var COMPONENTS = {};
var PENDING = {};

var CSS_DEFS = {};
var JS_DEFS = {};



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

function $get(url, data, cb) {
  url = url.replace("//pkg", "/pkg");
  return reqwest({
    url: url,
    data: data,
    success: cb
  });
}

function bootload_factory(type, module_dict, postload) {
  var factory_emitter = new EventEmitter();

  var to_load = {};
  var pending = {};
  function add_pending(modules) {
    _.each(modules, function(m) {
      if (!pending[m]) {
        to_load[m] = true;
      }

      pending[m] = true;
    });
  }

  var issue_request = function() {
    if (!_.keys(to_load).length) {
      return;
    }

    var config = { data: { m: JSON.stringify(_.keys(to_load)) } };

    to_load = {};


    function handle_module_dict(data) {
      if (module_dict) {
        _.each(data, function(v, k) {

          v.module = k;

          if (postload) {
            v = postload(k, v);
          }

          module_dict[k] = v;
        });


        _.each(data, function(v, k) {
          factory_emitter.trigger(k, [module_dict[k]]);
        });

      }

    }

    var req = $get($P._url + "/pkg/" + type, config);
    req.then(handle_module_dict);

    req.fail(function(data) {
      console.error("Failed to load", data);
    });

  };

  var throttled_issue_request = _.throttle(issue_request, 10, { leading: false });

  return function bootload(modules, cb) {
    if (_.isString(modules)) {
      modules = [modules];
    }

    var loaded_modules = {};
    var necessary_modules = _.filter(modules, function(k) {
      if (module_dict[k]) {
        loaded_modules[k] = module_dict[k];
      }

      // Let's see if we can load these modules from localStorage

      return !module_dict[k];
    });

    if (!necessary_modules.length) {
      if (cb) {
        cb(loaded_modules);
      }

      return;
    }

    var after = _.after(necessary_modules.length, function() {
      cb(loaded_modules);
    });

    _.each(necessary_modules, function(m) {
      factory_emitter.once(m, function() {
        loaded_modules[m] = module_dict[m];
        after();
      });
    });

    add_pending(necessary_modules);

    throttled_issue_request();


  };
}

function register_resource_packager(name, def_dict, postload) {
  return bootload_factory(name, def_dict, postload);
}



var _bootloaders = {};
function load_requires_for_dirhash(dirhash, requires, cb) {
  if (!_bootloaders[dirhash]) {
    _bootloaders[dirhash] = bootload_factory(dirhash, {}, function(name, res) {
      define_raw(name, res, dirhash);

      return res;
    });
  }

  var needed = {};
  _.each(requires, function(r) {
    var fr = r;
    if (fr.indexOf("::") == -1) { fr = dirhash + "::" + r; }

    if (!_defined[fr]) { needed[r] = r; }
  });

  if (!_.keys(needed).length) {
    return cb();
  }

  _bootloaders[dirhash](needed, cb);
}

function split_requires(dirhash, requires) {
  var ret = {};
  var tokens, ds, m, ns;

  ret[dirhash] = [];
  _.each(requires, function(r) {
    if (r.indexOf("::") != -1) {
      tokens = r.split("::");
      ns = tokens[0];
      m = tokens[1];

      // TODO: remove this looping and replace with a
      // lookup in a dictionary
      var parent;
      _.each($P._namespaces, function(v, k) {
        _.each(v, function(hs, name) {
          if (hs == dirhash) {
            parent = k;
            return;
          }
        });
      });

      _.each($P._namespaces[parent], function(hs, name) {
        if (name == ns) {
          ds = hs;
        }
      });

      ret[ds] = ret[ds] || [];
      ret[ds].push(m);
    } else {
      ret[dirhash].push(r);
    }
  });



  return ret;
}


function load_requires(dirhash, requires, cb) {
  var split = split_requires(dirhash, requires);
  var after = _.after(_.keys(split).length, cb);

  _.each(split, function(requires, ds) {
    load_requires_for_dirhash(ds, requires, after);
  });
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

  $P._boot.pkg(component, function(res) {
    _.each(res, function(cmp, name) {
      if (cmp) { inject_css(component, cmp.css); }
    });
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

function make_component_class(name, res) {
  COMPONENTS[name] = res;
  load_requires(res.dirhash, res.requires || [], function() {
    if (res.js) {
      if (!res.exports) {
        var klass = $P._raw_import(res.js, name);
        res.exports = klass;
      }
    }

    if (PENDING[name]) {
      PENDING[name].forEach(function(cb) {
        if (cb) {
          cb(res);
        }
      });
    }

  });

  return res;
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

  $P._boot.pkg(componentName, function(name, res) {
    _.each(res, function(cmpName, cmp) {
      _.each(cmp.defines, function(v, k) { define_raw(k, v, cmp.dirhash); });

      make_component_class(cmpName, cmp);

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
$P._missing = function(m) {
  console.trace("Missing require:", m);
}
$P._raw_import = raw_import;
$P._inject_pagelet = inject_pagelet;
$P._components = LOADED_COMPONENTS;
$P._inject_css= inject_css;
$P._require_css = function(m) {
  if (_.isArray(m)) {
    _.each(m, add_component_css);
  } else {
    add_component_css(m);
  }
}
$P._cmps = COMPONENTS;


$P._boot = {
  pkg: register_resource_packager('components', COMPONENTS, make_component_class),
};
