from . import components, util
from .blueprint import simple_component

import os
import json

static_folder = simple_component.static_folder
d = lambda w: os.path.join(static_folder, w)

PRELUDE = {
    "underscore"           : d("vendor/underscore-min.js"),
    "reqwest"              : d("vendor/reqwest.min.js"),
    "EventEmitter"         : d("vendor/EventEmitter.js"),
    "pudgy/prelude"        : d("prelude.js"),
    "pudgy/loader"         : d("loader.js"),
}

PRELUDE_RAW = {
    "proxy-polyfill"       : d("vendor/proxy.min.js"),
}

PRELUDE_LINES = []

def use_jquery():
    PRELUDE["jquery"] = d("vendor/jquery-3.3.1.min.js")
    add_prelude_line("window.jQuery = require('jquery')")

def add_to_prelude(name, fname):
    PRELUDE[name] = fname

def add_prelude_line(line):
    PRELUDE_LINES.append(line)

@util.memoize
def make_prelude():
    with open(PRELUDE["pudgy/prelude"]) as f:
        loaderjs = f.read()

    out = [ loaderjs ]
    dirhash = components.CoreComponent.get_dirhash()
    out.append("require.__dirhash = '%s'" % (dirhash))

    for name in PRELUDE:
        fname = PRELUDE[name]
        if name == "pudgy/prelude":
            continue

        with open(fname) as f:

            line = f.read()
            js = json.dumps(line)
            line = """var _inj = { name: '%s', dirhash: '%s', js: %s }; define_raw(_inj.name, _inj.js, _inj.dirhash); """ % (name, dirhash, js)

            out.append(line)

    for name in PRELUDE_RAW:
        fname = PRELUDE_RAW[name]
        with open(fname) as f:
            line = f.read()
            out.append("// %s" % name)
            out.append(line)

    for line in PRELUDE_LINES:
        out.append(line)


    out.append("require('pudgy/loader')")

    return "\n".join(out)
