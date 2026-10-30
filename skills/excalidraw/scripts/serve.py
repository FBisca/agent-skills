"""Serve a folder on http://127.0.0.1:8765 with CORS, so a page on excalidraw.com can fetch the split JSON.

Usage: python3 -I serve.py <dir>   (run in the background; stop it when the render loop is done)
"""
import http.server
import os
import sys

os.chdir(sys.argv[1])


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def log_message(self, *args):
        pass


http.server.HTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
