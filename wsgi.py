from kddit import app, load_config
import os

root = os.path.dirname(os.path.realpath(__file__))

load_config(root)

import kddit.routes

application = app
