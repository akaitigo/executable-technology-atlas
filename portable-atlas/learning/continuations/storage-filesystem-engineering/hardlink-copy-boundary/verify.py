#!/usr/bin/env python3
"""Independent saved-result comparison; never imports or runs experiment.py."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent

def verify(r):
    expected = json.loads((ROOT/"expected.json").read_text())
    checks=[]
    def same(label,a,b):
        if type(a) is not type(b) or a!=b:
            raise AssertionError(label)
        checks.append(label)
    same("schema",r["schema"],"atlas.hardlink-copy.observation.v1")
    for file in ["expected.json","HAND_TRACE.md","experiment.py","verify.py"]:
        same("source binding: "+file,r["source_bindings"][file],hashlib.sha256((ROOT/file).read_bytes()).hexdigest())
    same("complete",r["collection_complete"],True)
    same("unexpected errors",r["unexpected_errors"],[])
    same("timeout",r["timeout"],False)
    same("attempt",r["attempt"],1);same("retry",r["retry"],0)
    same("limits",r["limits"],{"max_names":3,"distinct_regular_files":2,"max_bytes_per_file":6,"timeout_seconds":5})
    same("phase order",[p["id"] for p in r["phases"]],[p["id"] for p in expected["phases"]])
    identity={}
    for observed,fixed in zip(r["phases"],expected["phases"]):
        same(observed["id"]+" exact names",sorted(observed["files"]),["alias","copy","original"])
        for name,wanted in fixed["files"].items():
            item=observed["files"][name];label=observed["id"]+"/"+name
            same(label+" exists",item["exists"],wanted is not None)
            if wanted is None:
                same(label+" errno",item["errno_name"],"ENOENT")
                continue
            pair=(item["identity"]["dev"],item["identity"]["ino"])
            same(label+" identity integer",all(type(n) is int for n in pair),True)
            symbol=wanted["identity"]
            if symbol in identity:
                same(label+" same-run identity",pair,identity[symbol])
            else:
                identity[symbol]=pair
            same(label+" nlink",item["nlink"],wanted["nlink"])
            same(label+" full bytes",bytes.fromhex(item["read_hex"]),bytes.fromhex(wanted["hex"]))
            same(label+" length",item["size"],6);same(label+" read length",item["read_bytes"],6)
    same("two separate identities",identity["A"]!=identity["B"],True)
    same("same owned filesystem",identity["A"][0],identity["B"][0])
    phases={p["id"]:p["files"] for p in r["phases"]}
    same("failure leaves state unchanged",phases["linked_and_copied"],phases["duplicate_link_rejected"])
    same("one expected failure",len(r["expected_failures"]),1)
    failure=r["expected_failures"][0]
    for k in ["operation","exception_type","errno_name"]:
        same("expected failure "+k,failure[k],expected["expected_failure"][k])
    same("expected failure distinct status",failure["outcome"],"expected_failure")
    operations=["create_original","create_hardlink","copy_content_to_new_file","duplicate_link","overwrite_alias_in_place","overwrite_copy_in_place","unlink_original_name"]
    same("finite operation order",[e["operation"] for e in r["events"]],operations)
    same("six normal operations",sum(e["outcome"]=="normal" for e in r["events"]),6)
    same("one expected failed operation",sum(e["outcome"]=="expected_failure" for e in r["events"]),1)
    for e in r["events"]:
        if "write_bytes" in e:
            same(e["operation"]+" write length",e["write_bytes"],6)
    same("copy initially read all input",r["events"][2]["read_hex"],"414c5048410a")
    same("remaining names before cleanup",r["owned_names_before_cleanup"],["alias.bin","copy.bin"])
    same("cleanup",r["cleanup_complete"],True)
    same("low priority",r["priority"]["after"]>=10,True)
    same("no fsync",r["fsync_called"],False)
    same("no broad claims",r["claims"],expected["claims"])
    return checks

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("usage: python3 -B verify.py observations/<attempt>/run.json")
    raw=Path(sys.argv[1]).read_bytes()
    try:
        checks=verify(json.loads(raw))
        print(json.dumps({"passed":True,"check_count":len(checks),"checks":checks,"observation_sha256":hashlib.sha256(raw).hexdigest(),"new_os_experiment":False},indent=2))
    except (AssertionError,KeyError,TypeError,ValueError) as error:
        print(json.dumps({"passed":False,"error":str(error),"new_os_experiment":False}));raise SystemExit(1)
