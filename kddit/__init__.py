from bottle import Bottle, request

app = Bottle()


@app.hook('before_request')
def strip_path():
    request.environ['PATH_INFO'] = request.environ['PATH_INFO'].rstrip('/')


def load_config(root):
    app.config.load_config(f'{root}/app.ini')
