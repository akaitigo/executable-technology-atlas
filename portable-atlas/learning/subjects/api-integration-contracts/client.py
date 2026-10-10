#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Client checks only the fixed lesson contract, not arbitrary JSON Schema."""
import json
import math


def integer(value):
    return type(value) is int or (type(value) is float and math.isfinite(value) and value.is_integer())


def evaluate(status,content_type,body,contract):
    steps=[]
    def step(gate,passed,detail):
        steps.append({"gate":gate,"verdict":"pass" if passed else "reject","detail":detail})
    def result(code,accepted=False,item=None):
        return {"outcome":code,"accepted":accepted,"item":item,"steps":steps}
    route=status in (contract["success_status"],contract["error_status"])
    step("status",route,str(status))
    if not route:
        return result("status-rejected")
    media=content_type.split(";",1)[0].strip().lower()
    step("content-type",media==contract["media_type"],media)
    if media!=contract["media_type"]:
        return result("media-rejected")
    try:
        def invalid_constant(value):
            raise ValueError("non-JSON constant: "+value)
        value=json.loads(body.decode("utf-8"),parse_constant=invalid_constant)
    except (ValueError,UnicodeError):
        step("json",False,"invalid or empty JSON")
        return result("json-rejected")
    step("json",True,"decoded JSON")
    if status==contract["error_status"]:
        error=value.get("error") if type(value) is dict else None
        valid=type(error) is dict and all(type(error.get(k)) is str and bool(error[k]) for k in ("code","message"))
        step("error-schema",valid,"error.code + error.message must be nonempty strings")
        return result("handled-api-error" if valid else "error-schema-rejected")
    schema=contract["success_schema"]
    if type(value) is not dict or any(k not in value for k in schema["required"]):
        step("success-schema",False,"required id/name missing or not object")
        return result("required-rejected")
    valid=integer(value["id"]) and value["id"]>=schema["properties"]["id"]["minimum"]
    valid=valid and type(value["name"]) is str and len(value["name"])>=schema["properties"]["name"]["minLength"]
    valid=valid and ("note" not in value or type(value["note"]) is str)
    step("success-schema",valid,"id integer>=1, name nonempty string, optional note string; other fields tolerated")
    return result("accepted" if valid else "type-rejected",valid,{"id":value["id"],"name":value["name"]} if valid else None)
