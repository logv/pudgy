import components

import os

PRELUDE = [ 
    "loader.js", 
    "vendor/jquery-3.3.1.min.js",
    "vendor/underscore.js",
    "vendor/backbone.js"
]

def make_prelude():
    static_folder = components.simple_component.static_folder
    out = []

    for p in PRELUDE:
        fname = os.path.join(static_folder, p)
        with open(fname) as f:
            out.append(f.read())


    return "\n".join(out)
