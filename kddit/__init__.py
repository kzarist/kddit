from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from . import settings

__all__ = ['app']

app = FastAPI()
app.mount('/static', StaticFiles(directory=f'{settings.ROOT}/static'), name='static')
