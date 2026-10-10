"""Atlas: saved-value checks against preimplementation literal table; no producer import."""
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
            for i, value in enumerate(expected):
                eq(actual[i], value, label + "." + str(i))
        elif actual != expected:
            raise AssertionError(label + ": value mismatch")
    fixture = json.loads((ROOT / "cases.json").read_text())["cases"]
    expected = json.loads((ROOT / "expected.json").read_text())["cases"]
    eq([c["id"] for c in data["cases"]], [c["id"] for c in fixture], "case set/order")
    for actual, case, hand in zip(data["cases"], fixture, expected):
        body = (ROOT / case["bodyFile"]).read_bytes()
        request = {"transportStatus": case["transportStatus"], "mediaType": case["mediaType"],
                   "bodyUtf8": body.decode("utf-8"), "bodyHex": body.hex()}
        eq(actual["input_before"], request, case["id"] + ".before")
        eq(actual["input_after"], request, case["id"] + ".after")
        eq(actual["bodySha256"], hashlib.sha256(body).hexdigest(), case["id"] + ".bytes")
        for mode in ("strict", "fault"):
            eq(actual[mode], hand[mode], case["id"] + "." + mode)
    for key, value in {"transportMeasured": False, "uriFetches": 0, "businessOperations": 0}.items():
        eq(data[key], value, key)
    return checks


def verify(data):
    count = check(data)
    tests = [
        ("missing-case", lambda d: d["cases"].pop()),
        ("transport-rewritten", lambda d: d["cases"][3]["fault"].update(transportStatus=200)),
        ("hold-disappears", lambda d: d["cases"][3]["strict"].update(decision="success")),
        ("held-value-adopted", lambda d: d["cases"][3]["strict"].update(chosenStatus=200)),
        ("translated-title-as-type", lambda d: d["cases"][5]["strict"].update(problemType="数量が正しくありません")),
        ("string-member-used", lambda d: d["cases"][4]["strict"].update(bodyStatus=422)),
        ("bool-number-confusion", lambda d: d.update(uriFetches=False)),
        ("input-bytes-changed", lambda d: d["cases"][0]["input_after"].update(bodyUtf8="{}\n")),
    ]
    results = []
    for name, modify in tests:
        altered = copy.deepcopy(data)
        modify(altered)
        try:
            check(altered)
        except (AssertionError, KeyError, TypeError, IndexError) as error:
            results.append({"id": name, "rejected": True, "reason": str(error)})
        else:
            raise AssertionError("mutation not detected: " + name)
    return {"Atlas": "保存した計算結果の照合", "passed": True, "checks": count,
            "mutations": results, "producerReexecuted": False,
            "limits": "8 alterations of saved results, not full input-schema or RFC conformance coverage"}
