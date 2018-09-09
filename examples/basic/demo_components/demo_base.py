import os
import pydgeon

class DemoDir(pydgeon.Component):
    BASE_DIR = os.path.dirname(os.path.realpath(__file__))

