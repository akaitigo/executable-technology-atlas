#!/usr/bin/env python3
"""Atlas: one bounded calculation of the six fixed input lassos."""
import hashlib,json,os,platform,resource,sys
from pathlib import Path
from fairness import graph_record,analyze
ROOT=Path(__file__).resolve().parent

def emit(value):print(json.dumps(value,ensure_ascii=False,sort_keys=True),flush=True)
def main():
    resource.setrlimit(resource.RLIMIT_CPU,(2,2))
    emit({'kind':'environment','project':'Atlas','python':sys.version,'executable':sys.executable,
          'platform':platform.platform(),'nice':os.getpriority(os.PRIO_PROCESS,0),
          'cpu_limit_seconds':list(resource.getrlimit(resource.RLIMIT_CPU)),'workers_created':0})
    path=ROOT/'inputs/lassos.json';cases=json.loads(path.read_text())['cases']
    graph=graph_record();graph['input_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();emit(graph)
    for case in cases:emit(analyze(case))
    emit({'kind':'batch-complete','case_count':len(cases),'retry_count':0})
if __name__=='__main__':main()
