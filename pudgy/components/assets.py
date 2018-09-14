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
    def render_file(cls, filename, error_if_missing=False):
        try:
            with open(filename, "r") as f:
                js = cls.transform(f.read())
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

class JSAsset(AssetLoader):
    EXT="js"


class CssAsset(AssetLoader):
    EXT="css"

    @classmethod
    def inject_css(cls,css):
        return 'var _inj = %s;\n $C._inject_css("", _inj.css);' % json.dumps({ "css": css })

    @classmethod
    def transform(cls, css):
        return cls.inject_css(css)

class SassAsset(CssAsset):
    EXT="sass"

    @classmethod
    def transform(cls, css):
        css = sass.compile(string=css)
        return cls.inject_css(css)
