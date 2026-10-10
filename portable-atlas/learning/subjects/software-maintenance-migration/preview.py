"""Read-only task-owned loopback preview; dynamic port and Ctrl-C cleanup."""
import functools
import http.server
from pathlib import Path

ROOT = Path(__file__).resolve().parent


if __name__ == "__main__":
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        print(f"http://127.0.0.1:{server.server_port}/index.html", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
