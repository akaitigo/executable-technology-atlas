"""Atlas: exactly four owned loopback GETs; no retry or external destination."""
import copy
import hashlib
import http.client
import http.server
import json
import threading
import time
from pathlib import Path
from boundary import assess

ROOT = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def produce():
    manifest_bytes = (ROOT / "cases.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    before = copy.deepcopy(manifest)
    bodies = {c["id"]: (ROOT / c["bodyFile"]).read_bytes() for c in manifest["cases"]}
    for case in manifest["cases"]:
        body = bodies[case["id"]]
        if len(body) != case["bodyBytes"] or digest(body) != case["bodySha256"]:
            raise ValueError("fixture bytes changed")
    lookup = {c["path"]: c for c in manifest["cases"]}
    server_events = []

    class Handler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args):
            pass

        def do_GET(self):
            case = lookup.get(self.path)
            if case is None:
                self.send_error(404)
                return
            body = bodies[case["id"]]
            event = {"id": case["id"], "method": self.command, "path": self.path,
                     "requestHeaders": list(self.headers.items()), "intendedStatus": case["status"],
                     "declaredLength": case["contentLength"], "bodyLength": len(body),
                     "bodySha256": digest(body), "writtenBytes": None, "writeException": None}
            server_events.append(event)
            try:
                self.send_response_only(case["status"], case["reason"])
                self.send_header("Content-Type", case["contentType"])
                self.send_header("Content-Length", str(case["contentLength"]))
                self.send_header("Connection", "close")
                self.end_headers()
                event["writtenBytes"] = self.wfile.write(body)
                self.wfile.flush()
            except (OSError, ValueError) as exc:
                event["writeException"] = {"type": type(exc).__name__, "message": str(exc)}
            finally:
                self.close_connection = True
                event["handlerFinished"] = True

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    server.timeout = 2
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01},
                              name="atlas-owned-http-framing")
    observations = []
    failure = None
    thread_started = False
    try:
        thread.start()
        thread_started = True
        for case in manifest["cases"]:
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
            actual = None
            request = {"method": "GET", "path": case["path"],
                       "headers": {"Accept": "application/problem+json", "Accept-Encoding": "identity", "Connection": "close"}}
            observation = {"id": case["id"], "request": request, "response": None,
                           "assessment": None, "attempt": 1, "retry": 0, "connectionClosed": False}
            observations.append(observation)
            start = time.monotonic()
            try:
                connection.request(request["method"], request["path"], headers=request["headers"])
                actual = connection.getresponse()
                declared_headers = actual.headers.get_all("Content-Length", [])
                if len(declared_headers) != 1 or not declared_headers[0].isascii() or not declared_headers[0].isdigit():
                    raise ValueError("outside fixed single Content-Length contract")
                if actual.getheader("Transfer-Encoding") is not None:
                    raise ValueError("Transfer-Encoding outside fixture contract")
                declared = int(declared_headers[0])
                length_before = actual.length
                closed_before = actual.isclosed()
                body = b""
                read_exception = None
                try:
                    body = actual.read(8193)
                except http.client.IncompleteRead as exc:
                    body = exc.partial
                    read_exception = {"type": type(exc).__name__, "expectedAdditionalBytes": exc.expected}
                response = {"status": actual.status, "reason": actual.reason,
                            "headers": list(actual.getheaders()), "declaredLength": declared,
                            "contentType": actual.getheader("Content-Type", ""),
                            "bodyHex": body.hex(), "bodyLength": len(body), "bodySha256": digest(body),
                            "readCalls": 1, "readAmount": 8193, "readException": read_exception,
                            "apiLengthBeforeRead": length_before, "apiIsClosedBeforeRead": closed_before,
                            "apiRemainingAfterRead": actual.length, "apiIsClosedAfterRead": actual.isclosed()}
                observation["response"] = response
                observation["assessment"] = assess(declared, body, response["contentType"], read_exception)
            finally:
                if actual is not None:
                    actual.close()
                connection.close()
                observation["responseClosedAfterCleanup"] = actual is None or actual.isclosed()
                observation["connectionClosed"] = connection.sock is None
                observation["elapsedSeconds"] = time.monotonic() - start
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        if thread_started:
            server.shutdown()
        server.server_close()
        if thread_started:
            thread.join(timeout=2)
    cleanup = {"serverSocketClosed": server.socket.fileno() == -1, "threadAlive": thread.is_alive(),
               "allConnectionsClosed": all(x["connectionClosed"] for x in observations)}
    if not cleanup["serverSocketClosed"] or cleanup["threadAlive"] or not cleanup["allConnectionsClosed"]:
        failure = failure or {"type": "CleanupFailure", "message": "owned resources not fully closed"}
    modules = {}
    for name, module in (("http.client", http.client), ("http.server", http.server)):
        path = Path(module.__file__).resolve()
        modules[name] = {"path": str(path), "sha256": digest(path.read_bytes())}
    return {"Atlas": "有効JSONとHTTP本文の完了境界", "kind": "actual_owned_loopback_http",
            "transportMeasured": True, "externalRequests": 0, "browserLaunches": 0,
            "endpoint": {"host": "127.0.0.1", "port": port}, "readAmount": 8193, "bodyLimit": 8192,
            "inputBefore": before, "inputAfter": manifest, "fixtureBodySha256After": {k: digest(v) for k, v in bodies.items()},
            "observations": observations, "serverEvents": server_events, "cleanup": cleanup,
            "executionFailure": failure, "stdlibModules": modules,
            "scope": {"packetCapture": False, "timeoutExperiment": False, "allRFCCompliance": False,
                      "businessOperations": 0, "problemMemberPolicyRetested": False}}
