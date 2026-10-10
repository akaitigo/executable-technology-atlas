"""Independent tuple-chain hand/reference oracle; no writes, eval, or host AST."""
import copy
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import random
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit
from interpreter import CASES, add, analyze, call, fn, integer, let, run, var

ROOT = Path(__file__).resolve().parent


def digest(data): return "sha256:" + hashlib.sha256(data).hexdigest()
def fingerprint(): return {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in ROOT.rglob("*") if p.is_file()}


def normalize(value):
    if type(value) is int or value is None:
        return value
    if isinstance(value, dict):
        return {"kind": "closure", "param": value["param"], "body_path": value["body_path"]}
    return {"kind": "closure", "param": value[1], "body_path": value[3]}


class ReferenceFailure(Exception):
    def __init__(self, code, path): self.code, self.path = code, path


def reference(ast, dynamic=False):
    """Separate tuple-of-binding-groups interpreter. No production env/methods."""
    fuel = [64]
    searches, returns = [], []
    def evaluate(node, chain, path):
        if fuel[0] == 0: raise ReferenceFailure("evaluation-budget", path)
        fuel[0] -= 1
        kind = node["kind"]
        if kind == "Int":
            answer = node["value"]
        elif kind == "Var":
            inspected, found = [], False
            for group in chain:
                inspected.append([name for name, _ in group])
                for name, value in group:
                    if name == node["name"]:
                        answer, found = value, True
                        break
                if found: break
            searches.append({"node_path": path, "name": node["name"], "groups": inspected,
                             "found": found, "value": normalize(answer) if found else None})
            if not found: raise ReferenceFailure("unbound-name", path)
        elif kind == "Fn":
            answer = ("closure", node["param"], node["body"], path + ".body", chain)
        elif kind == "Let":
            initializer = evaluate(node["value"], chain, path + ".value")
            answer = evaluate(node["body"], (((node["name"], initializer),),) + chain, path + ".body")
        elif kind == "Call":
            function = evaluate(node["fn"], chain, path + ".fn")
            if type(function) is int: raise ReferenceFailure("not-callable", path)
            actual = evaluate(node["arg"], chain, path + ".arg")
            body_chain = (((function[1], actual),),) + (chain if dynamic else function[4])
            answer = evaluate(function[2], body_chain, function[3])
        elif kind == "Add":
            a = evaluate(node["left"], chain, path + ".left")
            b = evaluate(node["right"], chain, path + ".right")
            if type(a) is not int or type(b) is not int: raise ReferenceFailure("addition-type", path)
            answer = a + b
        returns.append({"node_path": path, "kind": kind, "value": normalize(answer)})
        return answer
    try:
        value = normalize(evaluate(ast, ((),), "$"))
        error = None
    except ReferenceFailure as failure:
        value, error = None, {"code": failure.code, "node_path": failure.path}
    return {"status": "error" if error else "passed", "value": value, "error": error,
            "searches": searches, "returns": returns, "evaluations": 64 - fuel[0]}


def node_at(ast, path):
    node = ast
    for key in path.split(".")[1:]: node = node[key]
    return node


def audit_trace(observed, ast, dynamic):
    ref = reference(ast, dynamic)
    assert observed["status"] == ref["status"] and normalize(observed["value"]) == ref["value"]
    assert observed["evaluations"] == ref["evaluations"]
    assert (None if observed["error"] is None else {k: observed["error"][k] for k in ["code", "node_path"]}) == ref["error"]
    frames, closures, searches, returns = {}, {}, [], []
    pending_call = None
    enters = 0
    for number, event in enumerate(observed["trace"], 1):
        assert event["step"] == number
        action, path, env_id, details = (event[k] for k in ["action", "node_path", "env_id", "details"])
        node = node_at(ast, path)
        if action == "frame-create":
            frame = details["frame"]
            assert frame["id"] == env_id == "e%d" % len(frames) and env_id not in frames
            assert frame["parent"] is None or frame["parent"] in frames
            if frame["reason"] == "root":
                assert number == 1 and frame["parent"] is None and frame["bindings"] == {}
            elif frame["reason"] == "parameter":
                assert pending_call is not None
                assert frame["parent"] == pending_call["chosen_parent"]
                assert frame["bindings"] == {pending_call["param"]: pending_call["argument"]}
                pending_call = None
            else:
                assert frame["reason"] == "let" and node["kind"] == "Let"
                assert list(frame["bindings"]) == [node["name"]]
                # initializer's final return is directly before the immutable extension.
                previous = observed["trace"][number - 2]
                assert previous["action"] == "return" and previous["node_path"] == path + ".value"
                assert frame["bindings"][node["name"]] == previous["details"]["value"]
                assert frame["parent"] == previous["env_id"]
            frames[env_id] = frame
        else:
            assert env_id in frames, "event uses unavailable frame"
        if action == "enter":
            enters += 1
            assert details == {"kind": node["kind"], "remaining": 64 - enters}
        elif action == "capture":
            closure = details["closure"]
            assert node["kind"] == "Fn"
            assert closure == {"closure": "c%d" % len(closures), "param": node["param"],
                               "body_path": path + ".body", "captured_env": env_id}
            closures[closure["closure"]] = closure
        elif action == "call-parent":
            assert node["kind"] == "Call" and pending_call is None
            closure = closures[details["closure"]]
            assert details["captured_env"] == closure["captured_env"] and details["param"] == closure["param"]
            assert details["caller_env"] == env_id
            assert details["chosen_parent"] == (env_id if dynamic else closure["captured_env"])
            prior = observed["trace"][number - 2]
            assert prior["action"] == "return" and prior["node_path"] == path + ".arg"
            assert details["argument"] == prior["details"]["value"]
            pending_call = details
        elif action in ["lookup", "lookup-miss"]:
            assert node["kind"] == "Var" and details["name"] == node["name"]
            current, checked = env_id, []
            while current is not None:
                checked.append(current)
                if details["name"] in frames[current]["bindings"]: break
                current = frames[current]["parent"]
            assert details["checked"] == checked, "lookup chain drift"
            found = current is not None
            assert (action == "lookup") == found
            value = frames[current]["bindings"][details["name"]] if found else None
            if found:
                assert details["resolved_env"] == current and details["value"] == value
            searches.append({"node_path": path, "name": details["name"],
                             "groups": [list(frames[f]["bindings"]) for f in checked],
                             "found": found, "value": normalize(value)})
        elif action == "return":
            assert details["kind"] == node["kind"]
            returns.append({"node_path": path, "kind": details["kind"], "value": normalize(details["value"])})
        elif action == "add":
            assert node["kind"] == "Add" and len(details["operands"]) == 2
            assert all(type(x) is int for x in details["operands"])
            assert sum(details["operands"]) == details["result"]
        elif action == "error":
            assert number == len(observed["trace"]) and details == observed["error"]
        else:
            assert action == "frame-create", "unknown action"
    assert searches == ref["searches"] and returns == ref["returns"], "independent environment/value trace mismatch"
    assert list(frames.values()) == observed["frames"] and list(closures.values()) == observed["closures"]
    assert enters == observed["evaluations"] and pending_call is None
    if observed["error"]:
        assert observed["value"] is None and observed["trace"][-1]["action"] == "error"
    else:
        assert observed["trace"][-1]["action"] == "return" and observed["trace"][-1]["details"]["value"] == observed["value"]


def check_record(record):
    assert record["attempts"] == 1 and record["retries"] == 0 and record["exit_code"] == 0
    assert record["input"] == CASES and record["started_at"] <= record["finished_at"]
    assert record["started_at"].endswith("+09:00") and set(record["environment"]) == {"python", "implementation", "os", "release", "architecture"}
    assert record["command"] == "python3 -B check.py" and record["publish_command"] == "python3 -B observe.py --write-evidence"
    assert set(record["source_hashes"]) == {"interpreter.py", "check.py", "observe.py", "verify.py", "sources.json"}
    for name, expected in record["source_hashes"].items(): assert digest((ROOT/name).read_bytes()) == expected, "source drift"
    for item in [record["raw_stdout"], record["raw_stderr"]] + record["artifacts"]: assert digest((ROOT/item["path"]).read_bytes()) == item["digest"], "artifact drift"
    assert record["raw_stdout"]["path"] == "evidence/stdout.json" and record["raw_stderr"]["path"] == "evidence/stderr.txt"
    assert (ROOT/"evidence/stderr.txt").read_bytes() == b""
    assert record["artifacts"][0]["classification"] == "actual-environment-trace-redraw-not-screenshot"
    result = record["result"]
    assert json.loads((ROOT/"evidence/stdout.json").read_bytes()) == result
    assert record["source_version"] == result["model_version"] == "bounded-closure-environment-v1"
    assert result["limits"] == {"ast_nodes": 64, "ast_depth": 16, "literal_abs": 1000, "name_length": 16, "evaluation_budget": 64}
    assert set(result["cases"]) == set(CASES)
    for name, case in result["cases"].items():
        assert case["input"] == CASES[name]
        for key, dynamic in [("normal", False), ("broken", True)]:
            observed = case[key]
            assert observed["policy"] == ("broken-dynamic-caller-parent" if dynamic else "lexical-definition-parent")
            if name in ["invalid_literal", "invalid_ast"]:
                assert observed["status"] == "rejected" and observed["value"] is None
                assert observed["trace"] == observed["frames"] == observed["closures"] == [] and observed["evaluations"] == 0
                assert observed["error"]["code"] == ("literal-limit" if name == "invalid_literal" else "name-shape")
            else:
                audit_trace(observed, case["input"], dynamic)


def check_links():
    class Links(HTMLParser):
        def __init__(self): super().__init__(); self.links=[]; self.ids=set()
        def handle_starttag(self, tag, attrs):
            values = dict(attrs)
            if "id" in values: self.ids.add(values["id"])
            if tag == "a" and "href" in values: self.links.append(values["href"])
            if tag in ["link", "script"]: self.links.append(values.get("src", values.get("href", "")))
    html = (ROOT/"index.html").read_text(); page=Links(); page.feed(html)
    readme=(ROOT/"README.md").read_text(); md=re.findall(r"\[[^\]]+\]\(([^)]+)\)",readme)
    count=0
    for link in page.links + md:
        url=urlsplit(link)
        if url.scheme: assert url.scheme in ["https", "data"]; continue
        if url.path:
            path=(ROOT/unquote(url.path)).resolve()
            assert path.is_relative_to(ROOT) and path.is_file(), "missing local link: " + link
            count+=1
        elif url.fragment: assert url.fragment in page.ids
    official = {item["url"] for item in json.loads((ROOT/"sources.json").read_text())["sources"]}
    assert official.issubset({urlsplit(u)._replace(fragment="").geturl() for u in page.links if u.startswith("https:")})
    for url in ["https://softwarefoundations.cis.upenn.edu/plf-current/Smallstep.html", "https://softwarefoundations.cis.upenn.edu/plf-current/Stlc.html"]:
        assert url in md and url in page.links
    assert "scope-roadmap" in page.ids and 'data-field-id="programming-language-foundations"' in html
    return count


def main():
    before=fingerprint(); record=json.loads((ROOT/"evidence/run.json").read_bytes()); check_record(record)
    data=(ROOT/"data.js").read_text(); prefix="window.SCOPE_OBSERVATION = "
    assert data.startswith(prefix) and data.endswith(";\n") and json.loads(data[len(prefix):-2]) == record
    hand={"capture":(10,20), "parameter_shadow":(7,7), "argument_caller":(30,40), "escaped_closure":(10,20), "let_initializer":(11,11), "literal_boundary":(0,0)}
    cases=record["result"]["cases"]
    for name, values in hand.items(): assert tuple(cases[name][k]["value"] for k in ["normal","broken"]) == values
    assert cases["caller_rescue"]["normal"]["error"]["code"] == "unbound-name" and cases["caller_rescue"]["broken"]["value"] == 20
    for key,parent,resolved,value in [("normal","e1","e1",10),("broken","e3","e3",20)]:
        events=cases["capture"][key]["trace"]
        capture=next(e for e in events if e["action"]=="capture")
        assert capture["details"]["closure"]["captured_env"]=="e1"
        parent_event=next(e for e in events if e["action"]=="call-parent")
        assert parent_event["details"]["chosen_parent"]==parent
        lookup=next(e for e in events if e["action"]=="lookup" and e["details"]["name"]=="x")
        assert lookup["env_id"]=="e4" and lookup["details"]["checked"]==["e4",resolved]
        assert lookup["details"]["resolved_env"]==resolved and lookup["details"]["value"]==value
    rng=random.Random(3101)
    for _ in range(200):
        outer,inner,argument=[rng.randrange(-100,101) for _ in range(3)]
        name=rng.choice(["x","a","outer"]); parameter=rng.choice(["u",name])
        ast=let(name,integer(outer),let("f",fn(parameter,add(var(name),var(parameter))),let(name,integer(inner),call(var("f"),integer(argument)))))
        for dynamic in [False,True]: audit_trace(run(ast,dynamic),ast,dynamic)
    for ast in [fn("u",integer(0)),let("x",integer(-1000),var("x")),integer(1000)]:
        for dynamic in [False,True]: audit_trace(run(ast,dynamic),ast,dynamic)
    at_depth=integer(0)
    for _ in range(15): at_depth=fn("u",at_depth)
    assert run(at_depth)["status"]=="passed"
    invalid=[None,{}, {"kind":"Unknown"}, {"kind":"Int","value":True},integer(1001), integer(-1001),var("X"),var("x"*17),var(""),fn(True,integer(0)),{**integer(0),"extra":1},fn("u",at_depth)]
    # balanced tree has 63 nodes; one extra Fn =64 is accepted, another =65 rejected.
    tree=integer(0)
    for _ in range(5): tree=add(copy.deepcopy(tree),copy.deepcopy(tree))
    assert run(fn("u",tree))["status"]=="passed"
    invalid.append(fn("u",fn("u",tree)))
    for ast in invalid:
        observed=run(ast)
        assert observed["status"]=="rejected" and observed["value"] is None and observed["trace"]==[]
    negative=0
    for target,field,value in [("call-parent","chosen_parent","e3"),("lookup","resolved_env","e3"),("lookup","value",20),("capture","closure",{})]:
        bad=copy.deepcopy(cases["capture"]["normal"])
        event=next(e for e in bad["trace"] if e["action"]==target and (target!="lookup" or e["details"]["name"]=="x"))
        event["details"][field]=value
        try: audit_trace(bad,CASES["capture"],False)
        except (AssertionError,KeyError): negative+=1
        else: raise AssertionError("mutated binding trace accepted")
    bad=copy.deepcopy(cases["unbound"]["normal"]); bad["value"]=0
    try: audit_trace(bad,CASES["unbound"],False)
    except AssertionError: negative+=1
    else: raise AssertionError("error promoted to 0")
    for field in ["source_hashes","raw_stdout"]:
        bad=copy.deepcopy(record)
        if field=="source_hashes": bad[field]["interpreter.py"]="sha256:bad"
        else: bad[field]["digest"]="sha256:bad"
        try: check_record(bad)
        except AssertionError: negative+=1
        else: raise AssertionError("digest mutation accepted")
    for script in ["check.py","observe.py"]:
        completed=subprocess.run([sys.executable,"-B",script],cwd=ROOT,capture_output=True,timeout=10)
        assert completed.returncode==0 and completed.stderr==b"" and completed.stdout==(ROOT/"evidence/stdout.json").read_bytes()
    completed=subprocess.run([sys.executable,"-B","check.py","--case","unbound"],cwd=ROOT,capture_output=True,timeout=10)
    assert completed.returncode==2 and json.loads(completed.stdout)["normal"]["error"]["code"]=="unbound-name"
    links=check_links()
    assert fingerprint()==before,"read-only contract violated"
    print("PASS: hand environment chain + independent tuple oracle / capture-parent / lookup / return / errors / provenance; generated=200 invalid=%d negative=%d read-only=3 local-links=%d roadmap/source-binding" % (len(invalid),negative,links))


if __name__=="__main__": main()
