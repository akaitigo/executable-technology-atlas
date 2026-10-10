"""Original bounded AST interpreter. Lexical semantics; dynamic is an intentional defect."""
import copy
from dataclasses import dataclass
import re

VERSION = "bounded-closure-environment-v1"
LIMITS = {"ast_nodes": 64, "ast_depth": 16, "literal_abs": 1000, "name_length": 16, "evaluation_budget": 64}


def integer(value): return {"kind": "Int", "value": value}
def var(name): return {"kind": "Var", "name": name}
def let(name, value, body): return {"kind": "Let", "name": name, "value": value, "body": body}
def fn(param, body): return {"kind": "Fn", "param": param, "body": body}
def call(function, argument): return {"kind": "Call", "fn": function, "arg": argument}
def add(left, right): return {"kind": "Add", "left": left, "right": right}

SELF = fn("s", call(var("s"), var("s")))
CASES = {
    "capture": let("x", integer(10), let("f", fn("u", var("x")), let("x", integer(20), call(var("f"), integer(0))))),
    "parameter_shadow": let("x", integer(10), let("f", fn("x", var("x")), let("x", integer(20), call(var("f"), integer(7))))),
    "argument_caller": let("x", integer(10), let("f", fn("u", add(var("x"), var("u"))), let("x", integer(20), call(var("f"), var("x"))))),
    "escaped_closure": let("f", call(fn("x", fn("u", var("x"))), integer(10)), let("x", integer(20), call(var("f"), integer(0)))),
    "let_initializer": let("x", integer(10), let("x", add(var("x"), integer(1)), var("x"))),
    "unbound": var("missing"),
    "caller_rescue": let("f", fn("u", var("x")), let("x", integer(20), call(var("f"), integer(0)))),
    "not_callable": call(integer(10), integer(0)),
    "addition_type": add(fn("u", var("u")), integer(1)),
    "literal_boundary": add(integer(-1000), integer(1000)),
    "invalid_literal": integer(1001),
    "invalid_ast": {"kind": "Fn", "param": True, "body": integer(0)},
    "fuel_boundary": call(SELF, SELF),
}


class ModelError(Exception):
    def __init__(self, code, path, message, env_id=None):
        self.code, self.path, self.message, self.env_id = code, path, message, env_id
        super().__init__(message)


def validate(ast):
    count = 0
    fields = {"Int": {"kind", "value"}, "Var": {"kind", "name"},
              "Let": {"kind", "name", "value", "body"}, "Fn": {"kind", "param", "body"},
              "Call": {"kind", "fn", "arg"}, "Add": {"kind", "left", "right"}}
    children = {"Int": [], "Var": [], "Let": ["value", "body"], "Fn": ["body"], "Call": ["fn", "arg"], "Add": ["left", "right"]}
    def visit(node, path, depth):
        nonlocal count
        count += 1
        if count > 64 or depth > 16:
            raise ModelError("ast-limit", path, "ASTは64 node / depth16まで")
        if not isinstance(node, dict) or type(node.get("kind")) is not str or node["kind"] not in fields or set(node) != fields[node["kind"]]:
            raise ModelError("ast-shape", path, "許可されたkindとexact fieldが必要")
        kind = node["kind"]
        if kind == "Int" and (type(node["value"]) is not int or not -1000 <= node["value"] <= 1000):
            raise ModelError("literal-limit", path, "literalは-1000..1000のinteger（bool不可）")
        for key in ["name", "param"]:
            if key in node and (type(node[key]) is not str or re.fullmatch(r"[a-z][a-z0-9_]{0,15}", node[key]) is None):
                raise ModelError("name-shape", path, "nameはASCII小文字開始の1..16文字")
        for key in children[kind]:
            visit(node[key], path + "." + key, depth + 1)
    visit(ast, "$", 1)
    return count


@dataclass
class Environment:
    id: str
    bindings: dict
    parent: object


@dataclass
class Closure:
    id: str
    param: str
    body: dict
    body_path: str
    captured: Environment


def serial(value):
    if isinstance(value, Closure):
        return {"closure": value.id, "param": value.param, "body_path": value.body_path, "captured_env": value.captured.id}
    return value


class Evaluator:
    def __init__(self, dynamic=False):
        self.dynamic = dynamic
        self.trace, self.frames, self.closures = [], [], []
        self.remaining = 64
        self.root = self.frame({}, None, "$", "root")

    def emit(self, action, path, env, **details):
        self.trace.append({"step": len(self.trace) + 1, "action": action, "node_path": path,
                           "env_id": env.id, "details": details})

    def frame(self, bindings, parent, path, reason):
        env = Environment("e%d" % len(self.frames), bindings, parent)
        record = {"id": env.id, "parent": parent.id if parent else None,
                  "bindings": {name: serial(value) for name, value in bindings.items()}, "reason": reason}
        self.frames.append(record)
        self.emit("frame-create", path, env, frame=copy.deepcopy(record))
        return env

    def lookup(self, name, env, path):
        checked, current = [], env
        while current is not None:
            checked.append(current.id)
            if name in current.bindings:
                value = current.bindings[name]
                self.emit("lookup", path, env, name=name, checked=checked,
                          resolved_env=current.id, value=serial(value))
                return value
            current = current.parent
        self.emit("lookup-miss", path, env, name=name, checked=checked)
        raise ModelError("unbound-name", path, "未束縛name: " + name, env.id)

    def evaluate(self, node, env, path):
        if self.remaining <= 0:
            raise ModelError("evaluation-budget", path, "64 node evaluationで停止。発散の数学的証明ではない", env.id)
        self.remaining -= 1
        kind = node["kind"]
        self.emit("enter", path, env, kind=kind, remaining=self.remaining)
        if kind == "Int":
            value = node["value"]
        elif kind == "Var":
            value = self.lookup(node["name"], env, path)
        elif kind == "Let":
            initializer = self.evaluate(node["value"], env, path + ".value")
            extended = self.frame({node["name"]: initializer}, env, path, "let")
            value = self.evaluate(node["body"], extended, path + ".body")
        elif kind == "Fn":
            value = Closure("c%d" % len(self.closures), node["param"], node["body"], path + ".body", env)
            self.closures.append(serial(value))
            self.emit("capture", path, env, closure=serial(value))
        elif kind == "Call":
            function = self.evaluate(node["fn"], env, path + ".fn")
            if not isinstance(function, Closure):
                raise ModelError("not-callable", path, "CallのfnがClosureではない", env.id)
            argument = self.evaluate(node["arg"], env, path + ".arg")
            parent = env if self.dynamic else function.captured
            self.emit("call-parent", path, env, closure=function.id, captured_env=function.captured.id,
                      caller_env=env.id, chosen_parent=parent.id, argument=serial(argument), param=function.param)
            activated = self.frame({function.param: argument}, parent, path, "parameter")
            value = self.evaluate(function.body, activated, function.body_path)
        elif kind == "Add":
            left = self.evaluate(node["left"], env, path + ".left")
            right = self.evaluate(node["right"], env, path + ".right")
            if type(left) is not int or type(right) is not int:
                raise ModelError("addition-type", path, "Addの両operandはintegerだけ", env.id)
            value = left + right
            self.emit("add", path, env, operands=[left, right], result=value)
        self.emit("return", path, env, kind=kind, value=serial(value))
        return value


def run(ast, dynamic=False):
    policy = "broken-dynamic-caller-parent" if dynamic else "lexical-definition-parent"
    try:
        validate(ast)
    except ModelError as error:
        return {"policy": policy, "status": "rejected", "value": None,
                "error": {"code": error.code, "node_path": error.path, "message": error.message},
                "trace": [], "frames": [], "closures": [], "evaluations": 0}
    evaluator = Evaluator(dynamic)
    value, error = None, None
    try:
        value = serial(evaluator.evaluate(ast, evaluator.root, "$"))
    except ModelError as failure:
        error = {"code": failure.code, "node_path": failure.path, "message": failure.message}
        evaluator.trace.append({"step": len(evaluator.trace) + 1, "action": "error", "node_path": failure.path,
                                "env_id": failure.env_id, "details": error})
    return {"policy": policy, "status": "error" if error else "passed", "value": value,
            "error": error, "trace": evaluator.trace, "frames": evaluator.frames,
            "closures": evaluator.closures, "evaluations": 64 - evaluator.remaining}


def analyze(ast):
    return {"input": copy.deepcopy(ast), "normal": run(ast), "broken": run(ast, True)}


def batch():
    return {"model_version": VERSION, "classification": "original-finite-AST-interpreter-not-general-language-runtime",
            "limits": LIMITS, "semantics": "immutable let frames; single-parameter fn; lexical parent; call-by-value left-to-right; integer Add; no eval/exec",
            "cases": {name: analyze(ast) for name, ast in CASES.items()}}
