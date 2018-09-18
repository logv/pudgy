from . import components
from .blueprint import simple_component

import os
import json

static_folder = simple_component.static_folder
d = lambda w: os.path.join(static_folder, w)

PRELUDE = {
    "underscore"           : d("vendor/underscore-min.js"),
    "reqwest"              : d("vendor/reqwest.min.js"),
    "pudgy/prelude"        : d("prelude.js"),
    "pudgy/loader"         : d("loader.js"),
}

PRELUDE_RAW = {
    "proxy-polyfill"       : d("vendor/proxy.min.js"),
}

PRELUDE_LINES = []

def add_to_prelude(name, fname):
    PRELUDE[name] = fname

def add_prelude_line(line):
    PRELUDE_LINES.append(line)

def make_prelude():
    with open(PRELUDE["pudgy/prelude"]) as f:
        loaderjs = f.read()

    out = [ loaderjs ]



    for name in PRELUDE:
        fname = PRELUDE[name]
        if name == "pudgy/prelude":
            continue

        with open(fname) as f:

            line = f.read()
            js = json.dumps(line)
            line = """var _inj = { name: '%s', js: %s }; define_raw(_inj.name, _inj.js); """ % (name, js)

            out.append(line)

    for name in PRELUDE_RAW:
        fname = PRELUDE_RAW[name]
        with open(fname) as f:
            line = f.read()
            out.append("// %s" % name)
            out.append(line)

    for line in PRELUDE_LINES:
        out.append(line)


    out.append("require('pudgy/loader')");

    return "\n".join(out)
