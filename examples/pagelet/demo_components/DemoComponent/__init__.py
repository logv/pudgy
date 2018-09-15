import pudgy
from ..demo_base import DemoDir

import time

class DemoComponent(DemoDir, pudgy.MustacheComponent, pudgy.SassComponent,
    pudgy.BackboneComponent, pudgy.ClientBridge, pudgy.Pagelet):
    def __prepare__(self):
        print("STARTING PAGELET", self, time.time())
        time.sleep(self.delay)
        print("FINISHED PAGELET", self, time.time())

    def set_delay(self, delay=0):
        self.delay = delay

