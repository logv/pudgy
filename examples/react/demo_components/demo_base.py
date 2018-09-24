import os
import pudgy

class DemoDir(pudgy.Component):
    BASE_DIR = os.path.dirname(os.path.realpath(__file__))
