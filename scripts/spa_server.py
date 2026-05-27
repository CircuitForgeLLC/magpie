#!/usr/bin/env python3
"""
Static SPA server with index.html fallback.

Python's built-in http.server returns 404 for any path that isn't a real
file, which breaks Vue Router's history-mode navigation. This server falls
back to index.html for any path that doesn't match a real file, letting the
client-side router handle the route.

Usage:
    python scripts/spa_server.py --port 8531 --directory frontend/dist
"""
import argparse
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler


class SPAHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Resolve the path to an actual filesystem path inside self.directory.
        full = self.translate_path(self.path)
        # If the path doesn't resolve to a real file, serve index.html instead.
        if not os.path.isfile(full):
            self.path = "/index.html"
        super().do_GET()

    def log_message(self, fmt, *args):
        # Suppress per-request noise; errors still surface.
        if int(args[1]) >= 400:
            super().log_message(fmt, *args)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8531)
    parser.add_argument("--directory", default="frontend/dist")
    args = parser.parse_args()

    os.chdir(args.directory)
    server = HTTPServer(("", args.port), SPAHandler)
    print(f"Serving {args.directory} on :{args.port} (SPA fallback enabled)")
    server.serve_forever()


if __name__ == "__main__":
    main()
