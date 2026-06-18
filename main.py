#!/usr/bin/env python3
"""
Entrypoint for running alexbers/mtprotoproxy on Koyeb.

Koyeb (especially on scale-to-zero / free-tier services) requires at
least one HTTP route it can health-check and route traffic to. The
MTProto proxy itself speaks raw TCP, not HTTP, so this entrypoint runs
two things side by side in the same container:

  1. A minimal HTTP server on port 8000, purely so Koyeb has a valid
     HTTP route to attach health checks to and to satisfy the
     "at least one route is required" requirement.
  2. The real, unmodified mtprotoproxy (from the upstream repo cloned
     in the Dockerfile) on port 8080, which is the actual MTProto
     proxy your Telegram client connects to.

Koyeb's scale-to-zero / wake-on-request behavior only applies to the
HTTP route on port 8000. The MTProto proxy on 8080 runs continuously
as a background thread for as long as the container is alive.
"""

import os
import runpy
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HTTP_PORT = int(os.environ.get("HTTP_PORT", "8000"))


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"MTProto proxy is running.\n")

    def log_message(self, format, *args):
        # Silence default request logging to keep proxy logs clean
        pass


def run_http_server():
    server = ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), HealthCheckHandler)
    print(f"HTTP health-check server listening on 0.0.0.0:{HTTP_PORT}", file=sys.stderr, flush=True)
    server.serve_forever()


def run_mtproto_proxy():
    env_port = os.environ.get("PORT")
    if env_port:
        try:
            port = int(env_port)
            import config
            config.PORT = port
            print(f"Using PORT={port} from environment for MTProto proxy", file=sys.stderr, flush=True)
        except ValueError:
            print(f"Ignoring non-integer PORT env var: {env_port}", file=sys.stderr, flush=True)

    # Hand off execution to the real, upstream mtprotoproxy entrypoint
    # (mtprotoproxy.py in the cloned repo), so all of its actual proxy
    # logic runs unmodified.
    runpy.run_module("mtprotoproxy", run_name="__main__")


def main():
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    # Run the MTProto proxy on the main thread (it manages its own
    # asyncio event loop internally).
    run_mtproto_proxy()


if __name__ == "__main__":
    main()
