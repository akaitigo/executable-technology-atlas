# SPDX-License-Identifier: Apache-2.0
"""Original bounded expression language; no eval/exec or host-language parser."""
VERSION = "bounded-expression-recursive-descent-v1"
LIMITS = {"characters": 256, "integer_digits": 6, "parenthesis_depth": 16}
GRAMMAR = {"expr": "term ('+' term)*", "term": "atom ('*' atom)*", "atom": "INT | '(' expr ')'", "INT": "ASCII [0-9]{1,6}"}


class ExpressionError(ValueError):
    def __init__(self, source, offset, expected, found, phase, tokens=None, trace=None):
        super().__init__(f"{phase} error at offset {offset}: expected {expected}, found {found}")
        line = source.count("\n", 0, offset) + 1
        column = offset - source.rfind("\n", 0, offset)
        self.detail = {"phase": phase, "offset": offset, "line": line, "column": column,
                       "expected": expected, "found": found, "coordinate_system": "zero-based Unicode code-point offset; one-based line/column"}
        self.tokens, self.trace = tokens or [], trace or []


def tokenize(source):
    if not isinstance(source, str):
        raise ValueError("input must be a string")
    if len(source) > LIMITS["characters"]:
        raise ExpressionError(source, 256, "at most 256 characters", "input limit", "boundary")
    tokens, trace = [], []
    cursor = 0
    while cursor < len(source):
        char = source[cursor]
        if char in " \t\r\n":
            cursor += 1
            continue
        start = cursor
        if "0" <= char <= "9":
            while cursor < len(source) and "0" <= source[cursor] <= "9":
                cursor += 1
            if cursor-start > LIMITS["integer_digits"]:
                raise ExpressionError(source, start, "INT with at most 6 digits", source[start:cursor], "boundary", tokens, trace)
            kind, value = "INT", int(source[start:cursor])
        elif char in "+*()":
            cursor += 1
            kind, value = char, None
        else:
            raise ExpressionError(source, start, "ASCII digit, +, *, (, ), or whitespace", char, "lex", tokens, trace)
        token = {"kind": kind, "text": source[start:cursor], "start": start, "end": cursor, "value": value}
        tokens.append(token)
        trace.append({"phase": "token", "action": "emit", "token_index": len(tokens)-1, "span": [start, cursor], "label": f"{kind}: {token['text']}"})
    tokens.append({"kind": "EOF", "text": "", "start": len(source), "end": len(source), "value": None})
    trace.append({"phase": "token", "action": "emit", "token_index": len(tokens)-1, "span": [len(source),len(source)], "label": "EOF"})
    return tokens, trace


class Parser:
    def __init__(self, source, tokens, naive=False):
        self.source, self.tokens, self.naive = source, tokens, naive
        self.cursor, self.serial, self.depth = 0, 0, 0
        self.trace = []

    def peek(self):
        return self.tokens[self.cursor]

    def fail(self, expected):
        token = self.peek()
        raise ExpressionError(self.source, token["start"], expected, token["text"] or "EOF", "parse", self.tokens, self.trace)

    def consume(self, kind):
        token = self.peek()
        if token["kind"] != kind:
            self.fail(kind)
        self.trace.append({"phase":"parse", "action":"consume", "token_index":self.cursor,
                           "span":[token["start"],token["end"]], "label":f"consume {kind}"})
        if kind != "EOF":
            self.cursor += 1
        return token

    def node(self, kind, span, **fields):
        node = {"id":f"n{self.serial}","kind":kind,"span":span,**fields}
        self.serial += 1
        self.trace.append({"phase":"parse","action":"build","node_id":node["id"],"span":span,
                           "label":f"build {kind}"})
        return node

    def atom(self):
        token = self.peek()
        if token["kind"] == "INT":
            self.consume("INT")
            return self.node("Integer", [token["start"],token["end"]], value=token["value"])
        if token["kind"] == "(":
            if self.depth >= LIMITS["parenthesis_depth"]:
                self.fail("parenthesis depth <= 16")
            opening = self.consume("(")
            self.depth += 1
            child = self.expr()
            closing = self.consume(")")
            self.depth -= 1
            # Explicit grouping retained for the educational visualization.
            return self.node("Group", [opening["start"],closing["end"]], child=child)
        self.fail("INT or (")

    def term(self):
        left = self.atom()
        while self.peek()["kind"] == "*":
            op = self.consume("*")
            right = self.atom()
            left = self.node("Multiply", [left["span"][0],right["span"][1]], left=left, right=right, operator_span=[op["start"],op["end"]])
        return left

    def expr(self):
        # Intentionally altered grammar: all operators have equal precedence,
        # while grouping still works. This is NOT the declared normal grammar.
        operand = self.atom if self.naive else self.term
        left = operand()
        operators = ("+", "*") if self.naive else ("+",)
        while self.peek()["kind"] in operators:
            op = self.consume(self.peek()["kind"])
            right = operand()
            left = self.node("Add" if op["kind"] == "+" else "Multiply", [left["span"][0],right["span"][1]],
                             left=left,right=right,operator_span=[op["start"],op["end"]])
        return left

    def parse(self):
        tree = self.expr()
        self.consume("EOF")
        return tree


def evaluate(tree, trace):
    kind = tree["kind"]
    if kind == "Integer":
        result, operands = tree["value"], []
    elif kind == "Group":
        result = evaluate(tree["child"],trace)
        operands = [result]
    elif kind in ("Add", "Multiply"):
        left = evaluate(tree["left"],trace)
        right = evaluate(tree["right"],trace)
        operands = [left,right]
        result = left+right if kind == "Add" else left*right
    else:
        raise ValueError("unsupported AST kind")
    trace.append({"phase":"evaluate","action":kind,"node_id":tree["id"],"span":tree["span"],
                  "operands":operands,"result":result,"label":f"{kind} → {result}"})
    return result


def analyze(source):
    tokens, token_trace, parse_trace = [], [], []
    try:
        tokens, token_trace = tokenize(source)
        parser = Parser(source,tokens)
        tree = parser.parse()
        parse_trace = parser.trace
    except ExpressionError as error:
        if error.detail["phase"] == "parse":
            parse_trace = error.trace
        else:
            tokens, token_trace = error.tokens,error.trace
        event = {"phase":"error","action":"stop","span":[error.detail["offset"],error.detail["offset"]],
                 "label":f"{error.detail['phase']} error: expected {error.detail['expected']}"}
        return {"input":source,"status":"error","tokens":tokens,"ast":None,"value":None,"error":error.detail,
                "token_trace":token_trace,"parse_trace":parse_trace,"evaluation_trace":[],"timeline":token_trace+parse_trace+[event],"naive":None}
    evaluation_trace, naive_trace = [], []
    value = evaluate(tree,evaluation_trace)
    naive_parser = Parser(source,tokens,naive=True)
    naive_tree = naive_parser.parse()
    naive_value = evaluate(naive_tree,naive_trace)
    return {"input":source,"status":"passed","tokens":tokens,"ast":tree,"value":value,"error":None,
            "token_trace":token_trace,"parse_trace":parse_trace,"evaluation_trace":evaluation_trace,
            "timeline":token_trace+parse_trace+evaluation_trace,
            "naive":{"classification":"intentional equal-precedence grammar, not normal semantics","ast":naive_tree,
                     "value":naive_value,"trace":naive_trace}}


CASES = {"precedence":"2 + 3 * 4", "parentheses":"(2 + 3) * 4", "two_products":"2 * 3 + 4 * 5",
         "boundary":"0007 + 0 * 999999", "zero":"0", "missing_operand":"2 + * 3",
         "missing_close":"(2 + 3", "illegal_character":"2 + x", "adjacent_integers":"2 3", "multiline_error":"2 +\n * 3"}


def experiment():
    return {"model_version":VERSION,"grammar":GRAMMAR,"limits":LIMITS,"cases":{name:analyze(source) for name,source in CASES.items()}}
