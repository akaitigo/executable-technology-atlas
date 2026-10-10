# SPDX-License-Identifier: Apache-2.0
"""Read-only by default; --write-evidence explicitly publishes a fresh run."""
import argparse
import hashlib
import html
import json
import os
import platform
import subprocess
import sys
import tempfile
from datetime import datetime,timezone,timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(raw):
    return "sha256:"+hashlib.sha256(raw).hexdigest()


def save(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as file:
        file.write(raw)
        temporary = file.name
    os.replace(temporary,path)


def tree_svg(case):
    nodes,edges = [],[]
    leaves = 0
    def place(node,depth):
        nonlocal leaves
        children = [node["child"]] if node["kind"]=="Group" else ([node["left"],node["right"]] if node["kind"]!="Integer" else [])
        positions = [place(child,depth+1) for child in children]
        if positions:
            x = sum(p[0] for p in positions)/len(positions)
        else:
            x = 90+leaves*210
            leaves += 1
        y = 126+depth*95
        for cx,cy in positions:
            edges.append(f'<line x1="{x}" y1="{y+22}" x2="{cx}" y2="{cy-22}" stroke="#889b8c" stroke-width="2"/>')
        label = str(node["value"]) if node["kind"]=="Integer" else {"Add":"+","Multiply":"*","Group":"( )"}[node["kind"]]
        nodes.append(f'<rect x="{x-36}" y="{y-24}" width="72" height="48" rx="9" fill="#fff" stroke="#3d604a"/><text x="{x}" y="{y+7}" text-anchor="middle" font-size="23">{label}</text>')
        return x,y
    place(case["ast"],0)
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="720" height="430" viewBox="0 0 720 430" role="img" aria-labelledby="title desc">'
            '<title id="title">Expression AST redrawn from actual parser output</title><desc id="desc">Multiply subtree grouped below addition, not source-order evaluation.</desc>'
            '<rect width="720" height="430" rx="18" fill="#edf2ec"/><g font-family="sans-serif" fill="#22432e">'
            f'<text x="28" y="42" font-size="25">{html.escape(case["input"])} : AST evaluation = {case["value"]}</text>'
            f'<text x="28" y="69" font-size="15">実Python parser出力の再描画 / naive左から = {case["naive"]["value"]}</text>'
            +''.join(edges)+''.join(nodes)+'<text x="28" y="400" font-size="14">*のsubtreeを評価してから+へ。captureではない。</text></g></svg>')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-evidence",action="store_true",help="explicitly update raw run, data.js and generated diagram")
    args = parser.parse_args()
    started = datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")
    completed = subprocess.run([sys.executable,"-B","check.py"],cwd=HERE,capture_output=True,timeout=10,check=True)
    if not args.write_evidence:
        sys.stdout.buffer.write(completed.stdout)
        return
    result = json.loads(completed.stdout)
    diagram = tree_svg(result["cases"]["precedence"]).encode()
    run = {"schema_version":1,"classification":"actual-bounded-Python-interpreter-not-production-compiler",
           "started_at":started,"finished_at":datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds"),
           "command":"python3 -B check.py","publish_command":"python3 -B observe.py --write-evidence","attempts":1,"retries":0,
           "environment":{"python":platform.python_version(),"implementation":platform.python_implementation(),"os":platform.system(),"release":platform.release(),"architecture":platform.machine()},
           "input":{name:case["input"] for name,case in result["cases"].items()},"source_version":result["model_version"],
           "source_hashes":{name:sha((HERE/name).read_bytes()) for name in ("language.py","check.py","observe.py","verify.py","sources.json")},
           "raw_stdout":{"path":"evidence/stdout.json","digest":sha(completed.stdout)},"raw_stderr":{"path":"evidence/stderr.txt","digest":sha(completed.stderr)},
           "artifacts":[{"path":"evidence/precedence-ast.svg","digest":sha(diagram),"classification":"actual-parser-AST-redraw-not-screenshot"}],
           "exit_code":completed.returncode,"result":result}
    raw = (json.dumps(run,ensure_ascii=False,indent=2)+"\n").encode()
    save(HERE/"evidence/stdout.json",completed.stdout)
    save(HERE/"evidence/stderr.txt",completed.stderr)
    save(HERE/"evidence/precedence-ast.svg",diagram)
    save(HERE/"evidence/run.json",raw)
    save(HERE/"data.js",b"window.EXPRESSION_OBSERVATION = "+raw.rstrip()+b";\n")
    print("Observed:",run["finished_at"],run["environment"])
    for name,case in result["cases"].items():
        print(name,case["value"],"naive="+str(case["naive"]["value"]) if case["naive"] else case["error"])


if __name__ == "__main__":
    main()
