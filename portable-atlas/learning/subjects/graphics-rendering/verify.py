"""Read-only by default. --record NAME creates one new, never-overwritten run."""
import argparse
import copy
import datetime
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import platform
import re
import sys
sys.dont_write_bytecode = True
from raster import render, png

ROOT = Path(__file__).resolve().parent
SOURCES = ["raster.py","verify.py","scenes.json","index.html","lesson.js","serve.mjs","scope.json"]
def digest(data):
    return hashlib.sha256(data).hexdigest()
def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()
def triangles_for(case, scenes):
    if "refs" in case:
        return [copy.deepcopy(scenes["triangles"][ref]) for ref in case["refs"]]
    if "reverseOf" in case:
        parent = next(c for c in scenes["cases"] if c["id"] == case["reverseOf"])
        return list(reversed(triangles_for(parent, scenes)))
    return copy.deepcopy(case["triangles"])


def oracle_pixel(x, y, triangles, mode):
    # Independent area-partition containment + solved plane, not renderer edge
    # weights. Exact tie rule is part of the declared shared contract.
    p = (F(2*x+1,2), F(2*y+1,2))
    winner, winner_z = None, None
    def det(a,b,c):
        return a[0]*(b[1]-c[1])+b[0]*(c[1]-a[1])+c[0]*(a[1]-b[1])
    for t in triangles:
        v = [(F(a),F(b),F(z)) for a,b,z in t["vertices"]]
        area = det(*v)
        if area == 0:
            continue
        if abs(det(p,v[1],v[2]))+abs(det(v[0],p,v[2]))+abs(det(v[0],v[1],p)) != abs(area):
            continue
        if area < 0:
            v[1], v[2] = v[2], v[1]
        include = True
        for i in range(3):
            a,b = v[i],v[(i+1)%3]
            if det(a,b,p)==0 and min(a[0],b[0])<=p[0]<=max(a[0],b[0]) and min(a[1],b[1])<=p[1]<=max(a[1],b[1]):
                if not (b[1]<a[1] or (b[1]==a[1] and b[0]>a[0])):
                    include=False
        if not include:
            continue
        a,b,c=v
        dx1,dy1,dz1=b[0]-a[0],b[1]-a[1],b[2]-a[2]
        dx2,dy2,dz2=c[0]-a[0],c[1]-a[1],c[2]-a[2]
        denominator=dx1*dy2-dx2*dy1
        zx=(dz1*dy2-dz2*dy1)/denominator
        zy=(dx1*dz2-dx2*dz1)/denominator
        z=a[2]+zx*(p[0]-a[0])+zy*(p[1]-a[1])
        if mode=="painter" or winner_z is None or z<winner_z:
            winner,winner_z=t["id"],z
    return winner, str(winner_z) if winner_z is not None else None


def execute():
    scenes=json.loads((ROOT/"scenes.json").read_text())
    results=[]
    checks=0
    for case in scenes["cases"]:
        triangles=triangles_for(case,scenes)
        entry={"id":case["id"],"label":case["label"],"input":{"width":scenes["width"],"height":scenes["height"],"triangles":triangles}}
        for mode in ("depth","painter"):
            result=render(scenes["width"],scenes["height"],triangles,mode)
            for pixel in result["pixels"]:
                expected=oracle_pixel(pixel["x"],pixel["y"],triangles,mode)
                assert (pixel["owner"],pixel["depthExact"])==expected, (case["id"],mode,pixel)
                for fragment in pixel["fragments"]:
                    if fragment["covered"]:
                        assert sum(F(w) for w in fragment["weights"])==1
                        assert 0 <= F(fragment["depthExact"]) <= 1
                checks+=1
            entry[mode]=result
        entry["differenceCount"]=sum(a["owner"]!=b["owner"] for a,b in zip(entry["depth"]["pixels"],entry["painter"]["pixels"]))
        results.append(entry)
    byid={r["id"]:r for r in results}
    def owners(id,mode):
        return [(p["owner"],p["depthExact"]) for p in byid[id][mode]["pixels"]]
    assert owners("normal-ab","depth")==owners("normal-ba","depth")
    assert owners("normal-ab","painter")!=owners("normal-ba","painter")
    assert byid["normal-ab"]["differenceCount"]>0 and byid["normal-ba"]["differenceCount"]>0
    assert owners("normal-ab","depth")==owners("winding-reversed","depth")
    assert byid["degenerate"]["depth"]["degenerateTriangles"]==["A"]
    assert all(p["owner"] is None for p in byid["all-outside"]["depth"]["pixels"])
    assert owners("shared-ab","depth")==owners("shared-ba","depth")
    shared=byid["shared-ab"]["depth"]["pixels"]
    assert sum(p["owner"] is not None for p in shared)==36
    assert all(sum(f["covered"] for f in p["fragments"])==1 for p in shared if 2<=p["x"]<8 and 2<=p["y"]<8)
    assert owners("equal-ab","depth")!=owners("equal-ba","depth"), "equal depth is first-wins, not order-independent"
    # Invalid input is rejected rather than silently clamped or indexed outside.
    rejects=[]
    base=triangles_for(scenes["cases"][0],scenes)
    for name,w,h,ts in [("zero-grid",0,12,base),("bool-grid",True,12,base),("oversized",33,12,base),("bad-depth",16,12,[{"id":"A","vertices":[[1,1,"NaN"],[2,1,"0.2"],[1,2,"0.2"]]}]),("coordinate-out-of-contract",16,12,[{"id":"A","vertices":[[99,1,"0.2"],[2,1,"0.2"],[1,2,"0.2"]]}])]:
        try: render(w,h,ts)
        except (ValueError,ZeroDivisionError): rejects.append(name)
        else: raise AssertionError("invalid input accepted: "+name)
    return results,{"pixelOracleChecks":checks,"cases":len(results),"modesPerCase":2,"invalidInputsRejected":rejects,"invariants":["normal-depth-order-invariant","painter-order-sensitive","normal-painter-not-depth","winding-preserved","degenerate-rejected","off-grid-empty","shared-edge-once-36-pixels","equal-depth-first-wins-order-sensitive"]}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--record")
    parser.add_argument("--check")
    args=parser.parse_args()
    started=now()
    results,verification=execute()
    sources={f:digest((ROOT/f).read_bytes()) for f in SOURCES}
    output={"kind":"actual-python-cpu-rasterization","startedAt":started,"completedAt":now(),"environment":{"python":platform.python_version(),"implementation":platform.python_implementation(),"system":platform.system(),"machine":platform.machine()},"sourceHashes":sources,"contract":{"sample":"pixel center (x+1/2,y+1/2)","coordinates":"screen space, x right/y down, grid16x12", "coverage":"positive orientation; e>0 or e==0 and (dy<0 or dy==0 and dx>0)","depth":"screen-linear rational z in [0,1]; smaller nearer; strict LESS; clear +infinity represented by null; equal depth keeps first", "outside":"only viewport sample positions considered; not homogeneous clipping", "numeric":"exact Fraction; no GPU floating precision claim"},"verification":verification,"results":results,"artifacts":{}}
    if args.check:
        p=Path(args.check)
        if not re.fullmatch(r"observations/[a-z0-9-]+/run.json",str(p)): raise ValueError("check only module-local run")
        saved=json.loads((ROOT/p).read_text())
        assert saved["sourceHashes"]==sources, "stale captured sources"
        assert saved["results"]==results and saved["verification"]==verification, "saved CPU output changed"
        for f,metadata in saved["artifacts"].items():
            assert re.fullmatch(r"[a-z0-9-]+-(depth|painter).png",f)
            assert digest((ROOT/p.parent/f).read_bytes())==metadata["sha256"]
            case_id,mode=f.rsplit("-",1)
            mode=mode[:-4]
            result=next(r for r in results if r["id"]==case_id)
            assert digest(png(result[mode]))==metadata["sha256"], "PNG does not encode current CPU output"
        assert len(saved["artifacts"])==20
        output["checkedRecord"]=str(p)
    if args.record:
        if not re.fullmatch(r"[a-z][a-z0-9-]+",args.record): raise ValueError("new directory name required")
        (ROOT/"observations").mkdir(exist_ok=True)
        directory=ROOT/"observations"/args.record
        directory.mkdir()
        for result in results:
            for mode in ("depth","painter"):
                name=result["id"]+"-"+mode+".png"
                data=png(result[mode])
                with (directory/name).open("xb") as f: f.write(data)
                output["artifacts"][name]={"sha256":digest(data),"bytes":len(data),"width":16,"height":12,"format":"RGB PNG"}
        output["completedAt"]=now()
        with (directory/"run.json").open("x") as f: json.dump(output,f,ensure_ascii=False,indent=2); f.write("\n")
    print(json.dumps({"passed":True,"environment":output["environment"],"verification":verification,"sourceHashes":sources,"record":args.record,"checkedRecord":args.check},ensure_ascii=False,indent=2))

if __name__=="__main__":
    # Avoid pycache mutation during ordinary read-only checks; run with -B too.
    main()
