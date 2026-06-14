#!/usr/bin/env python3
"""
Static SPA server with index.html fallback and API reverse proxy.

Python's built-in http.server returns 404 for any path that isn't a real
file, which breaks Vue Router's history-mode navigation. This server falls
back to index.html for any path that doesn't match a real file, letting the
client-side router handle the route.

Requests to /api/* are forwarded to the FastAPI backend (--api-port).

Usage:
    python scripts/spa_server.py --port 8531 --directory frontend/dist --api-port 8532
"""
import argparse
import http.client
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler


class SPAHandler(SimpleHTTPRequestHandler):
    api_port: int = 8532

    # ------------------------------------------------------------------ #
    # API proxy
    # ------------------------------------------------------------------ #

    def _proxy_api(self) -> None:
        """Forward this request to the FastAPI backend and relay the response."""
        conn = http.client.HTTPConnection("127.0.0.1", self.api_port, timeout=120)
        body_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(body_len) if body_len else None
        # Strip hop-by-hop headers before forwarding.
        skip = {"host", "connection", "transfer-encoding"}
        fwd_headers = {k: v for k, v in self.headers.items() if k.lower() not in skip}
        try:
            conn.request(self.command, self.path, body=body, headers=fwd_headers)
            resp = conn.getresponse()
            self.send_response(resp.status)
            for header, value in resp.getheaders():
                if header.lower() not in ("transfer-encoding", "connection"):
                    self.send_header(header, value)
            self.end_headers()
            self.wfile.write(resp.read())
        except OSError as exc:
            self.send_error(502, f"API proxy error: {exc}")
        finally:
            conn.close()

    # ------------------------------------------------------------------ #
    # Request dispatch
    # ------------------------------------------------------------------ #

    def _is_api(self) -> bool:
        path = self.path.split("?", 1)[0]
        return path.startswith("/api/")

    def do_GET(self) -> None:
        if self._is_api():
            self._proxy_api()
            return
        full = self.translate_path(self.path)
        if not os.path.isfile(full):
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        if self._is_api():
            self._proxy_api()
            return
        self.send_error(405, "Method Not Allowed")

    def do_PUT(self) -> None:
        if self._is_api():
            self._proxy_api()
            return
        self.send_error(405, "Method Not Allowed")

    def do_PATCH(self) -> None:
        if self._is_api():
            self._proxy_api()
            return
        self.send_error(405, "Method Not Allowed")

    def do_DELETE(self) -> None:
        if self._is_api():
            self._proxy_api()
            return
        self.send_error(405, "Method Not Allowed")

    def log_message(self, fmt: str, *args: object) -> None:
        if int(args[1]) >= 400:
            super().log_message(fmt, *args)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8531)
    parser.add_argument("--directory", default="frontend/dist")
    parser.add_argument("--api-port", type=int, default=8532)
    args = parser.parse_args()

    SPAHandler.api_port = args.api_port
    os.chdir(args.directory)
    server = HTTPServer(("", args.port), SPAHandler)
    print(
        f"Serving {args.directory} on :{args.port} "
        f"(SPA fallback + API proxy → :{args.api_port})"
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
