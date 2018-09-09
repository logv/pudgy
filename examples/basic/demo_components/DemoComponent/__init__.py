import pydgeon
from ..demo_base import DemoDir

class DemoComponent(DemoDir, pydgeon.MustacheComponent, pydgeon.SassComponent,
    pydgeon.BackboneComponent, pydgeon.ClientBridge):
    pass

