from . import components

import os

PRELUDE = [
    "vendor/jquery-3.3.1.min.js",
    "vendor/underscore.js",
    "vendor/backbone.js",
    "loader.js",
    "vendor/proxy.min.js",
]

def make_prelude():
    static_folder = components.simple_component.static_folder
    out = []

    for p in PRELUDE:
        fname = os.path.join(static_folder, p)
        with open(fname) as f:
            out.append(f.read())


    return "\n".join(out)
