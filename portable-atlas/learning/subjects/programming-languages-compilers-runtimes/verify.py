# SPDX-License-Identifier: Apache-2.0
"""Read-only independent hand/tree and shunting-yard checks; no evidence writes."""
import copy
import hashlib
import json
import random
import re
import subprocess
import sys
from pathlib import Path

from language import CASES, analyze, experiment

HERE = Path(__file__).resolve().parent
HAND = {"precedence":(14,20),"parentheses":(20,20),"two_products":(26,50),"boundary":(7,6999993),"zero":(0,0)}
ERRORS = {"missing_operand":("parse",4,1,5),"missing_close":("parse",6,1,7),
          "illegal_character":("lex",4,1,5),"adjacent_integers":("parse",2,1,3),"multiline_error":("parse",5,2,2)}


def fingerprint():
    return {p.relative_to(HERE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.rglob("*") if p.is_file()}


def signature(node):
    if node["kind"] == "Integer":
        return ("Integer",node["value"])
    if node["kind"] == "Group":
        return signature(node["child"])
    return (node["kind"],signature(node["left"]),signature(node["right"]))


def oracle(source, equal_precedence=False):
    # Independent tokenizer and iterative operator/value stacks; no Parser,
    # tokenize(), or evaluate() from the implementation called here.
    raw = re.findall(r"[0-9]+|[+*()]|[^ \t\r\n]",source)
    values, operators = [], []
    precedence = {"+":1,"*":1 if equal_precedence else 2}
    expected_operand = True

    def reduce():
        op = operators.pop()
        right, left = values.pop(), values.pop()
        values.append((left[0]+right[0] if op=="+" else left[0]*right[0],
                       ("Add" if op=="+" else "Multiply",left[1],right[1])))

    for token in raw:
        if token.isascii() and token.isdigit():
            if not expected_operand:
                raise ValueError("oracle adjacent operands")
            values.append((int(token),("Integer",int(token))))
            expected_operand = False
        elif token == "(":
            if not expected_operand:
                raise ValueError("oracle missing operator")
            operators.append(token)
        elif token == ")":
            if expected_operand:
                raise ValueError("oracle missing operand")
            while operators and operators[-1] != "(":
                reduce()
            if not operators:
                raise ValueError("oracle unmatched close")
            operators.pop()
        elif token in precedence:
            if expected_operand:
                raise ValueError("oracle missing operand")
            while operators and operators[-1] != "(" and precedence[operators[-1]] >= precedence[token]:
                reduce()
            operators.append(token)
            expected_operand = True
        else:
            raise ValueError("oracle illegal character")
    if expected_operand or "(" in operators:
        raise ValueError("oracle incomplete expression")
    while operators:
        reduce()
    if len(values) != 1:
        raise ValueError("oracle not one value")
    return values[0]


def check_case(case):
    source = case["input"]
    last = 0
    for index, token in enumerate(case["tokens"]):
        start,end = token["start"],token["end"]
        assert last <= start <= end <= len(source)
        assert not source[last:start].strip(" \t\r\n")
        assert source[start:end] == token["text"]
        if token["kind"] == "INT":
            assert re.fullmatch(r"[0-9]{1,6}",token["text"]) and token["value"] == int(token["text"])
        elif token["kind"] == "EOF":
            assert index == len(case["tokens"])-1 and start == end == len(source)
        else:
            assert token["kind"] == token["text"] and token["kind"] in "+*()"
        last = end
    assert case["timeline"][:len(case["token_trace"])] == case["token_trace"]
    for event in case["timeline"]:
        start,end = event["span"]
        assert 0 <= start <= end <= len(source)
    if case["status"] == "error":
        assert case["ast"] is None and case["value"] is None and not case["evaluation_trace"] and case["naive"] is None
        err = case["error"]
        assert err["line"] == source.count("\n",0,err["offset"])+1
        assert err["column"] == err["offset"]-source.rfind("\n",0,err["offset"])
        assert case["timeline"][-1]["phase"] == "error"
        try:
            oracle(source)
        except ValueError:
            pass
        else:
            # Resource limits are distinct from syntax validity.
            assert err["phase"] == "boundary" or "depth" in err["expected"]
        return
    expected, tree = oracle(source)
    assert case["value"] == expected and signature(case["ast"]) == tree
    naive_value, naive_tree = oracle(source,True)
    assert case["naive"]["value"] == naive_value and signature(case["naive"]["ast"]) == naive_tree
    assert case["timeline"] == case["token_trace"] + case["parse_trace"] + case["evaluation_trace"]
    assert len(case["token_trace"]) == len(case["tokens"])
    def traverse(node):
        if node["kind"] == "Integer":
            assert int(source[slice(*node["span"])]) == node["value"]
            return [(node["id"],node["kind"],node["value"],node["span"],[])]
        if node["kind"] == "Group":
            assert source[node["span"][0]] == "(" and source[node["span"][1]-1] == ")"
            children = traverse(node["child"])
            return children + [(node["id"],node["kind"],children[-1][2],node["span"],[children[-1][2]])]
        assert source[slice(*node["operator_span"])] == ("+" if node["kind"]=="Add" else "*")
        left,right = traverse(node["left"]),traverse(node["right"])
        a,b = left[-1][2],right[-1][2]
        return left+right+[(node["id"],node["kind"],a+b if node["kind"]=="Add" else a*b,node["span"],[a,b])]
    events = traverse(case["ast"])
    assert len({event[0] for event in events}) == len(events)
    actual = [(e["node_id"],e["action"],e["result"],e["span"],e["operands"]) for e in case["evaluation_trace"]]
    assert actual == events
    builds = [e["node_id"] for e in case["parse_trace"] if e["action"] == "build"]
    assert len(builds) == len(set(builds)) and set(builds) == {e[0] for e in events}


def validate_result(result):
    assert set(result["cases"]) == set(CASES)
    for key,case in result["cases"].items():
        assert case["input"] == CASES[key]
        check_case(case)
        if key in HAND:
            assert case["status"] == "passed" and (case["value"],case["naive"]["value"]) == HAND[key]
        else:
            e = case["error"]
            assert (e["phase"],e["offset"],e["line"],e["column"]) == ERRORS[key]
    assert signature(result["cases"]["precedence"]["ast"]) == ("Add",("Integer",2),("Multiply",("Integer",3),("Integer",4)))


def main():
    before = fingerprint()
    run = json.loads((HERE/"evidence/run.json").read_text())
    for name,expected in run["source_hashes"].items():
        assert "sha256:"+hashlib.sha256((HERE/name).read_bytes()).hexdigest() == expected,name
    for key in ("raw_stdout","raw_stderr"):
        binding = run[key]
        assert "sha256:"+hashlib.sha256((HERE/binding["path"]).read_bytes()).hexdigest() == binding["digest"]
    assert run["result"] == json.loads((HERE/"evidence/stdout.json").read_text()) == experiment()
    ui = (HERE/"data.js").read_text().removeprefix("window.EXPRESSION_OBSERVATION = ").removesuffix(";\n")
    assert json.loads(ui) == run
    for binding in run["artifacts"]:
        assert "sha256:"+hashlib.sha256((HERE/binding["path"]).read_bytes()).hexdigest() == binding["digest"]
    validate_result(run["result"])
    rng = random.Random(20261005)
    def generated(depth):
        if depth==0 or rng.random()<.3:
            v = rng.randrange(10)
            return str(v),v
        a,x = generated(depth-1)
        b,y = generated(depth-1)
        op = rng.choice(("+","*"))
        return f"({a}{op}{b})",x+y if op=="+" else x*y
    for _ in range(100):
        text,expected = generated(4)
        case = analyze(text)
        check_case(case)
        assert case["value"] == expected
    invalid = ["", "()", "2+", "2**3", "2(3)", "(2+3", "2+3)", "-1", "2/3", "x", "２", "1000000", "("*17+"0"+")"*17, "0"*257]
    for text in invalid:
        assert analyze(text)["status"] == "error",text
    for text in ("0", "999999", "("*16+"0"+")"*16, "0"+" "*255):
        check_case(analyze(text))
    try:
        analyze(None)
    except ValueError:
        pass
    else:
        raise AssertionError("non-string input accepted")
    mutations = [
        lambda d:d["cases"]["precedence"].update(value=20),
        lambda d:d["cases"]["precedence"]["tokens"][0].update(start=1),
        lambda d:d["cases"]["precedence"]["evaluation_trace"].pop(),
        lambda d:d["cases"]["missing_operand"]["error"].update(offset=0),
        lambda d:d["cases"]["missing_operand"].update(value=0),
    ]
    for mutate in mutations:
        candidate = copy.deepcopy(run["result"])
        mutate(candidate)
        try:
            validate_result(candidate)
        except (AssertionError,ValueError):
            pass
        else:
            raise AssertionError("mutated evidence accepted")
    # Actual default and custom checker runs must leave every module byte intact.
    default = subprocess.run([sys.executable,"-B","check.py"],cwd=HERE,capture_output=True,check=True)
    assert json.loads(default.stdout) == run["result"]
    bad = subprocess.run([sys.executable,"-B","check.py","--expr","2 + * 3"],cwd=HERE,capture_output=True)
    assert bad.returncode == 2 and json.loads(bad.stdout)["error"]["offset"] == 4
    observe = subprocess.run([sys.executable,"-B","observe.py"],cwd=HERE,capture_output=True,check=True)
    assert json.loads(observe.stdout) == run["result"]
    assert fingerprint() == before,"read-only checker/verify mutated module files"
    print(f"PASS: hand/tree + independent shunting-yard / tokens+spans / AST+postorder trace / error position / raw+source+artifact+UI; generated=100 invalid={len(invalid)+1} evidence-negative={len(mutations)} read-only=3")


if __name__ == "__main__":
    main()
