"""Atlas: six immutable byte fixtures; model results separate from HTTP measurements."""
import copy
import hashlib
import json
from pathlib import Path
from consumer import consume

ROOT = Path(__file__).resolve().parent


def produce():
    fixture = json.loads((ROOT / "cases.json").read_text())
    rows = []
    for case in fixture["cases"]:
        body = (ROOT / case["bodyFile"]).read_bytes()
        request = {"transportStatus": case["transportStatus"], "mediaType": case["mediaType"],
                   "bodyUtf8": body.decode("utf-8"), "bodyHex": body.hex()}
        row = {"id": case["id"], "input_before": copy.deepcopy(request),
               "bodySha256": hashlib.sha256(body).hexdigest()}
        row["strict"] = consume(request["transportStatus"], request["mediaType"], body, "hold-mismatch")
        row["fault"] = consume(request["transportStatus"], request["mediaType"], body, "body-first")
        row["input_after"] = copy.deepcopy(request)
        rows.append(row)
    return {"Atlas": "固定応答のstatus解釈", "kind": "fixed_response_consumer",
            "transportMeasured": False, "uriFetches": 0, "businessOperations": 0, "cases": rows}
