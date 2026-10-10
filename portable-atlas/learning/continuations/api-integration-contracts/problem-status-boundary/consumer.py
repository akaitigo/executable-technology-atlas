"""Atlas: fixed-response consumer; no HTTP, URI fetch, or business operation."""
import json
import math

TYPE = "https://api.example.invalid/problems/invalid-quantity"
STANDARD_MEMBERS = {"type", "title", "status", "detail", "instance"}


def consume(transport_status, media_type, body_bytes, policy):
    if type(transport_status) is not int or transport_status != 422:
        raise ValueError("outside fixed transport status contract")
    if type(body_bytes) is not bytes or len(body_bytes) > 1024:
        raise ValueError("bounded bytes required")
    if media_type not in ("application/json", "application/problem+json"):
        raise ValueError("outside fixed media grammar")
    if policy not in ("hold-mismatch", "body-first"):
        raise ValueError("unknown consumer policy")
    def invalid_constant(value):
        raise ValueError("non-JSON numeric constant: " + value)
    body = json.loads(body_bytes.decode("utf-8"), parse_constant=invalid_constant)
    if type(body) is not dict:
        raise ValueError("JSON object required")
    output = {"format": "custom" if media_type == "application/json" else "problem",
              "transportStatus": transport_status, "bodyStatus": None,
              "statusRelation": "not-applicable", "chosenStatus": transport_status,
              "problemType": None, "title": None, "customCode": None,
              "ignoredMembers": [], "ignoredExtensions": [],
              "decision": "business-error", "reason": "transport-error-status"}
    if media_type == "application/json":
        error = body.get("error")
        if type(error) is not dict or any(type(error.get(k)) is not str or not error[k] for k in ("code", "message")):
            raise ValueError("outside fixed custom error contract")
        output.update(customCode=error["code"], title=error["message"])
        return output

    ignored = [key for key in ("type", "title", "detail", "instance") if key in body and type(body[key]) is not str]
    problem_type = body.get("type", "about:blank") if "type" not in ignored else "about:blank"
    if problem_type not in (TYPE, "about:blank"):
        raise ValueError("outside fixed absolute type identifiers")
    output.update(problemType=problem_type, title=body.get("title") if "title" not in ignored else None,
                  ignoredExtensions=sorted(set(body) - STANDARD_MEMBERS), statusRelation="absent")
    if "status" in body:
        value = body["status"]
        if type(value) not in (int, float):  # bool is not a JSON number for this contract.
            ignored.append("status")
            output["statusRelation"] = "ignored-type"
        else:
            if not math.isfinite(value) or value not in (200, 422):
                raise ValueError("outside fixed numeric status values")
            output["bodyStatus"] = value
            output["statusRelation"] = "match" if value == transport_status else "mismatch"
    output["ignoredMembers"] = sorted(ignored)
    if output["statusRelation"] == "mismatch":
        if policy == "hold-mismatch":
            output.update(decision="hold", reason="local-status-mismatch-policy")
        else:
            # Fault: only the consumer's chosen value changes, never the transport fixture.
            output.update(chosenStatus=output["bodyStatus"], decision="success",
                          reason="body-status-overrode-transport")
    return output
