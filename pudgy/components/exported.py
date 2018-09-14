import flask
import jinja2

# JinjaComponent: foo/foo.html
# BackboneComponent: foo/foo.js
# MustacheComponent: foo/foo.mustache
# SassComponent: foo/foo.css (runs it through sass pre-processor)
# CSSComponent:  foo/foo.css (doesn't run it through pre-processor)

# ClientBridge: requires foo/foo.js, exposes the client API on the server
# ServerBridge: requires foo/foo.js, exposes the server API on the client

# FlaskPage: takes template to render as named parameter
# BigJSPackage: renders the component as one large package instead of a split

from .components import Component, set_base_dir, validate_components

# templating
from .basic import MustacheComponent, JinjaComponent
# style
from .basic import SassComponent, CSSComponent, BigCSSPackage
# javascripts
from .basic import JSComponent, BigJSPackage


from .bridge import ClientBridge, ServerBridge
from .bigpipe import Pipeline, Pagelet
from .react import ReactComponent
from .backbone import BackboneComponent
from .page import Page, FlaskPage
