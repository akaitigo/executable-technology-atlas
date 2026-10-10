"""Atlas: bounded response assessment, independent of case IDs and hand tables."""
import json

BODY_LIMIT = 8192
GATES = ("framing", "budget", "media", "json")


def assess(declared_length, received_body, content_type, read_exception):
    if type(declared_length) is not int or declared_length < 0 or type(received_body) is not bytes:
        raise ValueError("outside fixed input contract")
    no_exception = read_exception is None
    complete = no_exception and len(received_body) == declared_length
    within_budget = len(received_body) <= BODY_LIMIT
    result = {
        "readDidNotRaise": no_exception,
        "completeResponse": complete,
        "withinBudget": within_budget,
        "exceptionOnlyComplete": no_exception,
        "exceptionOnlyIncorrect": no_exception != complete,
        "outcome": None,
        "stages": [{"gate": name, "verdict": "not-run"} for name in GATES],
        "decodedJSON": None,
    }

    def mark(index, passed):
        result["stages"][index]["verdict"] = "pass" if passed else "reject"
        return passed

    if not mark(0, complete):
        result["outcome"] = "incomplete-response"
        return result
    if not mark(1, within_budget):
        result["outcome"] = "body-limit-exceeded"
        return result
    if not mark(2, content_type == "application/problem+json"):
        result["outcome"] = "media-rejected"
        return result
    try:
        def invalid_constant(value):
            raise ValueError("non-JSON numeric constant")
        value = json.loads(received_body.decode("utf-8"), parse_constant=invalid_constant)
    except (ValueError, UnicodeError):
        mark(3, False)
        result["outcome"] = "json-rejected"
        return result
    mark(3, True)
    result.update(outcome="json-ready", decodedJSON=value)
    return result
