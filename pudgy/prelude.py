from . import components
from .blueprint import simple_component

import os

static_folder = simple_component.static_folder
PRELUDE = map(lambda w: os.path.join(static_folder, w), [
    "vendor/underscore-min.js",
    "vendor/reqwest.js",
    "loader.js",
    "vendor/proxy.min.js",
])

def add_to_prelude(fname):
    if not fname in PRELUDE:
        PRELUDE.append(fname)

def make_prelude():
    out = []

    for p in PRELUDE:
        with open(p) as f:
            out.append(f.read())


    return "\n".join(out)
