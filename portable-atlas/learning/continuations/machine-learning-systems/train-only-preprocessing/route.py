# SPDX-License-Identifier: Apache-2.0
import json,sys

def route(topic):
    if topic in ('preprocessing','train-only','leakage','standardization','1nn','cohort','trace'):
        return dict(status='supported',runner='python3 verify.py',ui='index.html',reference='README.md')
    return dict(status='unsupported',reference='coverage.json',reason='Synthetic local train-only preprocessing lesson; production training/evaluation/deployment unsupported')
if __name__=='__main__':print(json.dumps(route(sys.argv[1] if len(sys.argv)>1 else ''),ensure_ascii=False))
