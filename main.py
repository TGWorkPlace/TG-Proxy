#!/usr/bin/env python3
"""
Entrypoint for running alexbers/mtprotoproxy on Koyeb.

Koyeb requires at least one HTTP route it can health-check before it
will mark a deployment as healthy. The MTProto proxy itself speaks raw
TCP, not HTTP, so this entrypoint runs two things side by side:

  1. A minimal HTTP web server on port 8000 -- starts FIRST and
     immediately, so Koyeb's health check on this port succeeds right
     away and the deployment goes "healthy" without waiting on anything
     else.
  2. The real, unmodified mtprotoproxy (cloned from upstream in the
     Dockerfile) on port 8080 -- the actual MTProto proxy your
     Telegram client connects to. This runs in a background thread.

Order matters here: if the HTTP server starts late or on a background
thread that doesn't get scheduled promptly, Koyeb's health check can
time out and the deploy gets stuck on "starting". Starting the HTTP
server first, on the main thread, and only then launching the proxy
in the background avoids that.
"""

import os
import sys
import threading
import runpy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HTTP_PORT = int(os.environ.get("HTTP_PORT", "8000"))


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", "26")
        self.end_headers()
        self.wfile.write(b"MTProto proxy is running\n")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

    def log_message(self, format, *args):
        # Keep logs focused on the proxy itself, not health-check noise
        print(f"[http] {self.address_string()} - {format % args}", file=sys.stderr, flush=True)


def start_http_server():
    print(f"[http] starting web server on 0.0.0.0:{HTTP_PORT} ...", file=sys.stderr, flush=True)
    server = ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), HealthCheckHandler)
    print(f"[http] web server is up on 0.0.0.0:{HTTP_PORT}", file=sys.stderr, flush=True)
    return server


def run_mtproto_proxy_in_background():
    def _run():
        env_port = os.environ.get("PORT")
        if env_port:
            try:
                port = int(env_port)
                import config
                config.PORT = port
                print(f"[proxy] using PORT={port} from environment", file=sys.stderr, flush=True)
            except ValueError:
                print(f"[proxy] ignoring non-integer PORT env var: {env_port}", file=sys.stderr, flush=True)

        print("[proxy] launching mtprotoproxy ...", file=sys.stderr, flush=True)
        try:
            runpy.run_module("mtprotoproxy", run_name="__main__")
        except Exception as e:
            print(f"[proxy] mtprotoproxy crashed: {e}", file=sys.stderr, flush=True)

    thread = threading.Thread(target=_run, daemon=True, name="mtprotoproxy")
    thread.start()
    return thread


def main():
    # 1. Bring up the HTTP server first and on the main thread, so it is
    #    listening before Koyeb's first health-check probe arrives.
    http_server = start_http_server()

    # 2. Launch the actual MTProto proxy in a background thread once the
    #    HTTP server already exists.
    run_mtproto_proxy_in_background()

    # 3. Block forever serving HTTP requests on the main thread.
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        print("[http] shutting down", file=sys.stderr, flush=True)
        http_server.shutdown()


if __name__ == "__main__":
    main()
