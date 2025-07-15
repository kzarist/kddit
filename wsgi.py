from kddit import app, load_config
import kddit.routes  # noqa: F401
import os

root = os.path.dirname(os.path.realpath(__file__))

load_config(root)


application = app
