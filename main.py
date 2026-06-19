#!/usr/bin/env python3
"""
Entrypoint for running alexbers/mtprotoproxy on Koyeb.

IMPORTANT: mtprotoproxy.py calls signal.signal() during startup (to
handle SIGUSR1/SIGTERM/etc), and Python only allows signal.signal() to
be called from the main thread of the main interpreter. So the real
proxy MUST run on the main thread here, not in a background thread.

The HTTP health-check server (port 8000, for Koyeb's required route)
runs in a background thread instead -- it doesn't need signal handling,
so this is the correct way around.
"""
import sys
print("[boot] main.py process started", flush=True)

import os
import threading
import runpy
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HTTP_PORT = int(os.environ.get("HTTP_PORT", "8080"))

print(f"[boot] python={sys.version.split()[0]} HTTP_PORT={HTTP_PORT} PORT_env={os.environ.get('PORT')}",
      flush=True)


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"MTProto proxy is running\n")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

    def log_message(self, format, *args):
        print(f"[http] {self.address_string()} - {format % args}", flush=True)


def run_http_server_in_background():
    def _serve():
        try:
            print(f"[http] binding 0.0.0.0:{HTTP_PORT} ...", flush=True)
            server = ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), HealthCheckHandler)
            print(f"[http] listening on 0.0.0.0:{HTTP_PORT}", flush=True)
            server.serve_forever()
        except Exception:
            print("[http] HTTP server crashed:", flush=True)
            traceback.print_exc()

    thread = threading.Thread(target=_serve, daemon=True, name="http-health")
    thread.start()
    return thread


def main():
    # 1. Start the HTTP health-check server in the background first,
    #    so Koyeb's route/health check passes quickly.
    run_http_server_in_background()

    # 2. Run the real MTProto proxy on the MAIN thread -- required,
    #    because it installs signal handlers via signal.signal(),
    #    which only works on the main thread.
    mtproto_port_env = os.environ.get("MTPROTO_PORT")
    if mtproto_port_env:
        try:
            port = int(mtproto_port_env)
            import config
            config.PORT = port
            print(f"[proxy] using PORT={port} from MTPROTO_PORT env var", flush=True)
        except ValueError:
            print(f"[proxy] ignoring non-integer MTPROTO_PORT env var: {mtproto_port_env}", flush=True)

    print("[proxy] launching mtprotoproxy on main thread ...", flush=True)
    runpy.run_module("mtprotoproxy", run_name="__main__")


if __name__ == "__main__":
    main()
