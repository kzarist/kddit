from kddit import app
import os

root = os.path.dirname(os.path.realpath(__file__))

print(f'Loading kddit application from {root}')

app.config.load_config(f'{root}/app.ini')

import kddit.routes  # noqa: E402, F401

application = app
