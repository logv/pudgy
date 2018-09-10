from . import components
from .blueprint import simple_component

import os

PRELUDE = [
    "vendor/jquery-3.3.1.min.js",
    "vendor/underscore.js",
    "loader.js",
    "vendor/proxy.min.js",
]

def make_prelude():
    static_folder = simple_component.static_folder
    out = []

    for p in PRELUDE:
        fname = os.path.join(static_folder, p)
        with open(fname) as f:
            out.append(f.read())


    return "\n".join(out)
