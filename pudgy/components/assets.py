from .components import *
from . import proxy

from .. import util

import flask
import dotmap
import json

class AssetLoader(Component):
    EXT="???"
    @classmethod
    def find_file(cls, fname, basedir, cls_dir):
        fname = fname.strip("'\"")
        if fname.endswith(cls.EXT):
            fname,ext = os.path.splitext(fname)

        if fname[0] == ".":
            jsp = "%s.%s" % (os.path.join(cls_dir, basedir, fname), cls.EXT)
        else:
            jsp = "%s.%s" % (os.path.join(cls_dir, fname), cls.EXT)

        return jsp

    @classmethod
    def render_file_to_js(cls, filename, error_if_missing=False):
        try:
            with open(filename, "r") as f:
                js = cls.transform_and_wrap_in_js(f.read())
                return js
        except IOError as e:
            if error_if_missing:
                raise e

        return ""

    @classmethod
    def match(cls, fname):
        return fname.endswith(".%s" % cls.EXT)

    @classmethod
    def transform(cls, js):
        return js

    @classmethod
    def transform_and_wrap_in_js(cls, js):
        dirhash = cls.get_dirhash()
        basehash = cls.get_basehash()
        return "require.__basehash = '%s'\nrequire.__dirhash = '%s';\n %s" % (basehash, dirhash, cls.transform(js))

class JSAsset(AssetLoader):
    EXT="js"


class CssAsset(AssetLoader):
    EXT="css"

    @classmethod
    def scopename(cls, css):
        import hashlib
        m = hashlib.md5()
        m.update(css)

        hashed = m.hexdigest()[:8]

        return "scoped_" + hashed


    @classmethod
    def inject_css(cls,css, scope=""):
        if not scope:
            scope = cls.scopename(css)

        return """
            var _inj = %s;\n $P._inject_css(_inj.scope, _inj.css);
            module.exports.className = _inj.scope;

        """ % json.dumps({ "css": css, "scope": scope })

    @classmethod
    def transform(cls, css, scope=""):
        if scope:
            return sass.compile(string=".%s { %s }" % (scope, css))

        return sass.compile(string=css)

    @classmethod
    def transform_and_wrap_in_js(cls, css):
        scope = cls.scopename(css)
        css = cls.transform(css, scope=scope)
        return cls.inject_css(css, scope)


class SassAsset(CssAsset):
    EXT="sass"
