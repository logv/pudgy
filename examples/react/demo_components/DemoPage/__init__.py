import pudgy
from ..demo_base import DemoDir

class DemoPage(DemoDir, pudgy.ServerBridge, pudgy.FlaskPage,
    pudgy.BackboneComponent):
    pass

@DemoPage.api
def server_call(self, component=None):
    if component:
        component.call("handle_click", "SERVER AJAX")

    self.call("handle_data", data="some_custom_data")
    return { "some_data": "HANDLING DATA" }

