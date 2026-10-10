"""Atlas: read saved values against literal expectations; never import the experiment."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def check(data):
    checks = 0

    def eq(actual, expected, label):
        nonlocal checks
        checks += 1
        if type(actual) is not type(expected):
            raise AssertionError(label + ": exact type mismatch")
        if type(expected) is dict:
            if set(actual) != set(expected):
                raise AssertionError(label + ": keys mismatch")
            for key in expected:
                eq(actual[key], expected[key], label + "." + key)
        elif type(expected) is list:
            if len(actual) != len(expected):
                raise AssertionError(label + ": length mismatch")
            for index, value in enumerate(expected):
                eq(actual[index], value, label + "." + str(index))
        elif actual != expected:
            raise AssertionError(label + ": value mismatch")

    inputs = json.loads((ROOT / "cases.json").read_text())
    hand = json.loads((ROOT / "expected.json").read_text())["cases"]
    eq(data["inputBefore"], inputs, "input before")
    eq(data["inputAfter"], inputs, "input after")
    ids = [c["id"] for c in inputs["cases"]]
    eq([x["id"] for x in data["observations"]], ids, "received cases")
    eq([x["id"] for x in data["serverEvents"]], ids, "server cases")
    for observed, event, fixture, expected in zip(data["observations"], data["serverEvents"], inputs["cases"], hand):
        cid = fixture["id"]
        body = (ROOT / fixture["bodyFile"]).read_bytes()
        eq(observed["request"], {"method": "GET", "path": fixture["path"],
            "headers": {"Accept": "application/problem+json", "Accept-Encoding": "identity", "Connection": "close"}}, cid + ".request")
        response = observed["response"]
        for key, value in {"status": 422, "reason": "Unprocessable Content", "declaredLength": expected["declaredLength"],
                "contentType": "application/problem+json", "bodyHex": body.hex(), "bodyLength": expected["receivedLength"],
                "bodySha256": hashlib.sha256(body).hexdigest(), "readCalls": 1, "readAmount": 8193,
                "readException": None, "apiLengthBeforeRead": expected["declaredLength"], "apiIsClosedBeforeRead": False,
                "apiRemainingAfterRead": expected["apiRemainingAfterRead"], "apiIsClosedAfterRead": expected["apiIsClosedAfterRead"]}.items():
            eq(response[key], value, cid + ".response." + key)
        eq(response["headers"], [["Content-Type", "application/problem+json"],
            ["Content-Length", str(expected["declaredLength"])], ["Connection", "close"]], cid + ".headers")
        keys = ("readDidNotRaise", "completeResponse", "withinBudget", "exceptionOnlyComplete",
                "exceptionOnlyIncorrect", "outcome", "stages", "decodedJSON")
        eq(observed["assessment"], {k: expected[k] for k in keys}, cid + ".assessment")
        for k, v in {"attempt": 1, "retry": 0, "connectionClosed": True, "responseClosedAfterCleanup": True}.items():
            eq(observed[k], v, cid + "." + k)
        for k, v in {"method": "GET", "path": fixture["path"], "intendedStatus": 422,
                     "declaredLength": expected["declaredLength"], "bodyLength": len(body),
                     "bodySha256": hashlib.sha256(body).hexdigest(), "writtenBytes": len(body),
                     "writeException": None, "handlerFinished": True}.items():
            eq(event[k], v, cid + ".server." + k)
        request_headers = dict(event["requestHeaders"])
        for k, v in observed["request"]["headers"].items():
            eq(request_headers[k], v, cid + ".requestHeader." + k)
        eq(request_headers["Host"], "127.0.0.1:" + str(data["endpoint"]["port"]), cid + ".Host")
        eq(data["fixtureBodySha256After"][cid], hashlib.sha256(body).hexdigest(), cid + ".fixture unchanged")
    eq(data["cleanup"], {"serverSocketClosed": True, "threadAlive": False, "allConnectionsClosed": True}, "cleanup")
    eq(data["executionFailure"], None, "execution failure")
    eq(data["transportMeasured"], True, "actual HTTP")
    eq(data["externalRequests"], 0, "external requests")
    eq(data["browserLaunches"], 0, "browser launches")
    eq(data["bodyLimit"], 8192, "body limit metadata")
    eq(data["readAmount"], 8193, "read amount metadata")
    eq(data["endpoint"]["host"], "127.0.0.1", "loopback")
    if type(data["endpoint"]["port"]) is not int or not 0 < data["endpoint"]["port"] < 65536:
        raise AssertionError("invalid owned port")
    eq(sorted(data["stdlibModules"]), ["http.client", "http.server"], "required stdlib modules")
    for module in data["stdlibModules"].values():
        eq(sorted(module), ["path", "sha256"], "stdlib record fields")
        eq(module["sha256"], hashlib.sha256(Path(module["path"]).read_bytes()).hexdigest(), "observed stdlib version")
    return checks


def verify(data):
    count = check(data)
    tests = [
        ("missing-case", lambda d: d["observations"].pop()),
        ("declared-replaced-with-received", lambda d: d["observations"][1]["response"].update(declaredLength=105)),
        ("no-exception-as-complete", lambda d: d["observations"][1]["assessment"].update(completeResponse=True)),
        ("rejected-json-retained", lambda d: d["observations"][1]["assessment"].update(decodedJSON={})),
        ("extra-read-hidden", lambda d: d["observations"][1]["response"].update(readCalls=2)),
        ("over-limit-accepted", lambda d: d["observations"][3]["assessment"].update(outcome="json-ready")),
        ("changed-input-type", lambda d: d["inputAfter"].update(readCallsPerResponse=True)),
        ("unclosed-server", lambda d: d["cleanup"].update(serverSocketClosed=False)),
        ("stdlib-records-omitted", lambda d: d.update(stdlibModules={})),
        ("budget-metadata-altered", lambda d: d.update(bodyLimit=8193)),
    ]
    mutations = []
    for name, modify in tests:
        changed = copy.deepcopy(data)
        modify(changed)
        try:
            check(changed)
        except (AssertionError, KeyError, TypeError, IndexError) as error:
            mutations.append({"id": name, "rejected": True, "reason": str(error)})
        else:
            raise AssertionError("undetected saved-value mutation: " + name)
    return {"Atlas": "保存した4応答の照合", "passed": True, "checks": count, "mutations": mutations,
            "targetReexecuted": False, "scope": "Ten changes of saved records, not all HTTP/input failures."}
