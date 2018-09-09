import pydgeon
from ..demo_base import DemoDir

class DemoPage(DemoDir, pydgeon.ServerBridge, pydgeon.FlaskPage,
    pydgeon.BackboneComponent):
    pass

@DemoPage.api
def server_call(self, component=None):
    if component:
        component.append_html("<br />ADDED FROM SERVER AJAX CALL")
        component.call("handle_click", "SERVER AJAX")
    self.call("handle_data", data="some_custom_data")
    return { "some_data": "HANDLING DATA" }

