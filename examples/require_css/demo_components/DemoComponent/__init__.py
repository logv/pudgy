import pudgy
from ..demo_base import DemoDir

class DemoComponent(DemoDir, pudgy.MustacheComponent,
    pudgy.BackboneComponent, pudgy.ClientBridge):
    pass

