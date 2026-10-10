# SPDX-License-Identifier: Apache-2.0
import json,sys

def route(topic):
    if topic in ['bell','mixture','partial-trace','joint-probability','basis','coherence','branch-average']:
        return dict(status='supported',runner='python3 verify.py',ui='index.html',reference='README.md')
    return dict(status='unsupported',reference='coverage.json',reason='Finite ideal two-qubit CPU model; quantum hardware, Bell inequality and quantum advantage unimplemented')
if __name__=='__main__':print(json.dumps(route(sys.argv[1] if len(sys.argv)>1 else ''),ensure_ascii=False))
