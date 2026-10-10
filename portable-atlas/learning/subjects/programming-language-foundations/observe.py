"""Default stdout-only; --write-evidence explicitly observes and publishes a run."""
import argparse
import datetime
import hashlib
from html import escape
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def digest(data): return "sha256:" + hashlib.sha256(data).hexdigest()


def redraw(case):
    groups=[]
    for column,(key,title) in enumerate([("normal","LEXICAL / definition parent"),("broken","DEFECT / caller parent")]):
        result=case[key]
        event=next(e for e in result["trace"] if e["action"]=="lookup" and e["details"]["name"]=="x")
        frames={f["id"]:f for f in result["frames"]}
        x=24+column*450
        groups.append('<text x="%d" y="92" font-size="18">%s</text>'%(x,title))
        for index,env_id in enumerate(event["details"]["checked"]):
            frame=frames[env_id]; y=115+index*80
            text=env_id+' '+json.dumps(frame["bindings"],ensure_ascii=False)
            color="#deeadf" if key=="normal" else "#f7d8b0"
            groups.append('<rect x="%d" y="%d" width="400" height="48" rx="5" fill="%s"/><text x="%d" y="%d" font-size="18">%s</text>'%(x,y,color,x+14,y+30,escape(text)))
            if index+1<len(event["details"]["checked"]):
                groups.append('<path d="M%d %d v23 l-5 -6 m5 6 l5 -6" stroke="#24403b" fill="none"/>'%(x+50,y+50))
        groups.append('<text x="%d" y="300" font-size="18">x resolves in %s → %s</text>'%(x,event["details"]["resolved_env"],event["details"]["value"]))
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="920" height="380" viewBox="0 0 920 380">'
            '<rect width="920" height="380" fill="#f7f6ef"/><g fill="#24403b" font-family="monospace">'
            '<text x="24" y="35" font-size="24">Closure c0 captures e1 {x:10}</text>'
            '<text x="24" y="62" font-size="14">Same AST and argument u=0. Only activation parent differs. Search stops at first binding.</text>'
            +''.join(groups)+'<text x="24" y="352" font-size="13">Actual interpreter lookup trace redraw — NOT a screenshot or general language proof</text></g></svg>').encode()


def replace(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as file:
        file.write(data); temporary=file.name
    os.replace(temporary,path)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--write-evidence",action="store_true"); args=parser.parse_args()
    started=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec="seconds")
    result=subprocess.run([sys.executable,"-B","check.py"],cwd=ROOT,capture_output=True,timeout=10)
    if not args.write_evidence:
        sys.stdout.buffer.write(result.stdout);sys.stderr.buffer.write(result.stderr);return result.returncode
    if result.returncode: raise RuntimeError("checker failed; prior evidence retained")
    output=json.loads(result.stdout); diagram=redraw(output["cases"]["capture"])
    record={"schema_version":1,"classification":"actual-original-finite-closure-interpreter-run",
            "started_at":started,"finished_at":datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec="seconds"),
            "command":"python3 -B check.py","publish_command":"python3 -B observe.py --write-evidence","attempts":1,"retries":0,
            "environment":{"python":platform.python_version(),"implementation":platform.python_implementation(),"os":platform.system(),"release":platform.release(),"architecture":platform.machine()},
            "input":{key:case["input"] for key,case in output["cases"].items()},"source_version":output["model_version"],
            "source_hashes":{name:digest((ROOT/name).read_bytes()) for name in ["interpreter.py","check.py","observe.py","verify.py","sources.json"]},
            "raw_stdout":{"path":"evidence/stdout.json","digest":digest(result.stdout)},"raw_stderr":{"path":"evidence/stderr.txt","digest":digest(result.stderr)},
            "artifacts":[{"path":"evidence/environment-chain.svg","digest":digest(diagram),"classification":"actual-environment-trace-redraw-not-screenshot"}],
            "exit_code":result.returncode,"result":output}
    replace(ROOT/"evidence/stdout.json",result.stdout);replace(ROOT/"evidence/stderr.txt",result.stderr)
    replace(ROOT/"evidence/environment-chain.svg",diagram)
    replace(ROOT/"evidence/run.json",(json.dumps(record,ensure_ascii=False,indent=2)+"\n").encode())
    replace(ROOT/"data.js",("window.SCOPE_OBSERVATION = "+json.dumps(record,ensure_ascii=False)+";\n").encode())
    print(json.dumps({"published":True,"observed_at":started,"raw_digest":digest(result.stdout)},ensure_ascii=False));return 0


if __name__=="__main__":raise SystemExit(main())
