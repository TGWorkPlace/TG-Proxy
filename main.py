#!/usr/bin/env python3
"""
Entrypoint for running alexbers/mtprotoproxy on Koyeb.

This print happens at the very top, before any other imports run, so
that if something later fails to import, you still get *something* in
the logs proving the process actually started.
"""
import sys
print("[boot] main.py process started", file=sys.stderr, flush=True)
print("[boot] main.py process started", file=sys.stdout, flush=True)

import os
import threading
import runpy
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HTTP_PORT = int(os.environ.get("HTTP_PORT", "8000"))

print(f"[boot] python={sys.version.split()[0]} HTTP_PORT={HTTP_PORT} PORT_env={os.environ.get('PORT')}",
      file=sys.stderr, flush=True)


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
        print(f"[http] {self.address_string()} - {format % args}", file=sys.stderr, flush=True)


def start_http_server():
    print(f"[http] binding 0.0.0.0:{HTTP_PORT} ...", file=sys.stderr, flush=True)
    server = ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), HealthCheckHandler)
    print(f"[http] listening on 0.0.0.0:{HTTP_PORT}", file=sys.stderr, flush=True)
    return server


def run_mtproto_proxy_in_background():
    def _run():
        try:
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
            runpy.run_module("mtprotoproxy", run_name="__main__")
        except Exception:
            print("[proxy] mtprotoproxy crashed with exception:", file=sys.stderr, flush=True)
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()

    thread = threading.Thread(target=_run, daemon=True, name="mtprotoproxy")
    thread.start()
    return thread


def main():
    try:
        http_server = start_http_server()
    except Exception:
        print("[http] FAILED TO BIND HTTP SERVER:", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        raise

    run_mtproto_proxy_in_background()

    print("[boot] entering serve_forever() loop", file=sys.stderr, flush=True)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        print("[http] shutting down", file=sys.stderr, flush=True)
        http_server.shutdown()


if __name__ == "__main__":
    main()
