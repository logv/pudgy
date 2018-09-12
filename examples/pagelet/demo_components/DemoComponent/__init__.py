import pudgy
from ..demo_base import DemoDir

import time

class DemoComponent(DemoDir, pudgy.MustacheComponent, pudgy.SassComponent,
    pudgy.BackboneComponent, pudgy.ClientBridge, pudgy.Pagelet):
    pass
    def __prepare__(self):
        print("STARTING PAGELET", self, time.time())
        time.sleep(5)
        print("FINISHED PAGELET", self, time.time())

