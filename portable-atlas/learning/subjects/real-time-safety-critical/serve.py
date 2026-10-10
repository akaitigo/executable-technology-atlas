"""Dedicated module UI on an OS-selected loopback port. No RT policy changes."""
import sys
sys.dont_write_bytecode = True
import argparse
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
from runner import ROOT, CASES, observe, publish

HOST = "127.0.0.1"


class Handler(SimpleHTTPRequestHandler):
    def respond(self, status, data):
        raw = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        if self.path != "/api/run":
            self.respond(404, {"error": "unknown endpoint"})
            return
        expected_origin = "http://%s:%d" % (HOST, self.server.server_port)
        if self.headers.get("Origin") not in (None, expected_origin) or self.headers.get("Content-Type") != "application/json":
            self.respond(403, {"error": "module loopback JSON only"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 4096:
                raise ValueError("invalid request length")
            request = json.loads(self.rfile.read(size))
            if not isinstance(request, dict) or set(request) != {"case", "horizon"}:
                raise ValueError("invalid input fields")
            if request["horizon"] not in (12, 24, 36) or type(request["horizon"]) is not int:
                raise ValueError("UI horizon must be 12/24/36")
            payload = observe(request["case"], request["horizon"], ["HTTP POST", "/api/run", "module JSON inputs"])
            payload["comparison"] = [observe(case, request["horizon"], ["UI comparison", case]) for case in CASES]
            location = publish(payload, "ui")
            self.respond(200, {"payload": payload, "raw_path": str(location.relative_to(ROOT)) + "/result.json",
                               "metadata_path": str(location.relative_to(ROOT)) + "/metadata.json"})
        except (ValueError, TypeError, KeyError) as error:
            self.respond(400, {"error": str(error)})
        except OSError:
            self.respond(500, {"error": "publish failed; prior observations retained"})

    def do_GET(self):
        if self.path.startswith("/api/"):
            self.respond(405, {"error": "compute/record via explicit POST button"})
        elif self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        else:
            super().do_GET()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=0, help="0 lets OS choose an unused loopback port")
    args = parser.parse_args()
    server = HTTPServer((HOST, args.port), partial(Handler, directory=str(ROOT)))
    print("finite EDF simulator http://%s:%d (abstract ticks only)" % (HOST, server.server_port), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
