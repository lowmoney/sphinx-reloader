import time
from http.server import SimpleHTTPRequestHandler
from . import config


class ServerHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="./build", **kwargs)

    def _set_headers(self, code):
        self.send_response(code)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/__reloader__":
            if config.lastReload < config.lastBuild:
                config.lastReload = time.time()
                self._set_headers(205)
            else:
                self._set_headers(200)

        else:
            return super().do_GET()

    def log_request(self, *args, **kwargs):
        return