import pudgy
from ..demo_base import DemoDir

class DemoComponent(DemoDir, pudgy.MustacheComponent, pudgy.SassComponent,
    pudgy.BackboneComponent, pudgy.ClientBridge):
    pass

