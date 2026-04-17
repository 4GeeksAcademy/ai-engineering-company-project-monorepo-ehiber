import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.abspath(__file__))
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", "3000"))
    handler = partial(NoCacheHandler, directory=root_dir)

    with ThreadingHTTPServer((host, port), handler) as httpd:
        print(f"Serving {root_dir} on http://{host}:{port}")
        httpd.serve_forever()
