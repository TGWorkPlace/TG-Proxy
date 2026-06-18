#!/usr/bin/env python3
"""
Entrypoint for running alexbers/mtprotoproxy on Koyeb.

Koyeb injects a PORT environment variable for "Web" service types.
This proxy is a raw TCP service, so on Koyeb you should deploy it as a
"TCP" service and just set PORT = 8080 in config.py to match the
Dockerfile's EXPOSE. If Koyeb (or you) sets a PORT env var anyway, this
entrypoint will honor it and override config.py automatically, so you
don't have to keep both in sync by hand.
"""

import os
import runpy
import sys


def main():
    env_port = os.environ.get("PORT")
    if env_port:
        try:
            port = int(env_port)
            import config
            config.PORT = port
            print(f"Using PORT={port} from environment", file=sys.stderr, flush=True)
        except ValueError:
            print(f"Ignoring non-integer PORT env var: {env_port}", file=sys.stderr, flush=True)

    # Hand off execution to the real, upstream mtprotoproxy entrypoint
    # (mtprotoproxy.py in the cloned repo), so all of its actual proxy
    # logic runs unmodified.
    runpy.run_module("mtprotoproxy", run_name="__main__")


if __name__ == "__main__":
    main()
