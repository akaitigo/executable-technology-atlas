"""Module-only loopback UI. POST computation explicitly appends a unique raw record."""
import sys
sys.dont_write_bytecode = True
import copy
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
from urllib.parse import urlparse
from runner import ROOT, observe, publish

HOST, PORT = "127.0.0.1", 18773
ORIGIN = "http://%s:%d" % (HOST, PORT)
RESULTS = {}


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
        if self.headers.get("Origin") not in (None, ORIGIN) or self.headers.get("Content-Type") != "application/json":
            self.respond(403, {"error": "module loopback JSON request only"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 4096:
                raise ValueError("request length out of range")
            request = json.loads(self.rfile.read(size))
            if not isinstance(request, dict) or set(request) != {"case", "retries", "seed", "previous_id"}:
                raise ValueError("unexpected input fields")
            prior_id = request["previous_id"]
            if prior_id is not None and (not isinstance(prior_id, str) or prior_id not in RESULTS):
                raise ValueError("prior run is unavailable; first run fresh")
            previous = None if prior_id is None else RESULTS[prior_id]["payload"]["result"]
            payload = observe(request["case"], request["retries"], request["seed"], previous,
                              ["HTTP POST", "/api/run", "JSON module inputs"])
            payload["previous_artifact"] = None if prior_id is None else RESULTS[prior_id]["raw_path"]
            payload["comparison"] = [observe(case, request["retries"], request["seed"], command=["UI finite comparison", case]) for case in ("normal", "fail-once", "always-fail", "cycle")]
            location = publish(payload, "ui")
            run_id = location.name
            raw_path = str(location.relative_to(ROOT)) + "/result.json"
            RESULTS[run_id] = {"payload": copy.deepcopy(payload), "raw_path": raw_path}
            self.respond(200, {"run_id": run_id, "raw_path": raw_path, "metadata_path": str(location.relative_to(ROOT)) + "/metadata.json", "payload": payload})
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
            self.respond(400, {"error": str(error)})
        except OSError:
            self.respond(500, {"error": "artifact publish failed; previous observations unchanged"})

    def do_GET(self):
        if urlparse(self.path).path.startswith("/api/"):
            self.respond(405, {"error": "use explicit UI POST to compute and record"})
            return
        super().do_GET()


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), partial(Handler, directory=str(ROOT)))
    print("finite DAG simulator %s (CPU only)" % ORIGIN, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
