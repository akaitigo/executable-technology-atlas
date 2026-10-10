# SPDX-License-Identifier: Apache-2.0
def route(topic):
    if topic in ['write-through','write-back','dirty','eviction','flush','write-allocate']:
        return dict(status='supported',runner='python3 verify.py',ui='index.html',guide='README.md')
    return dict(status='unsupported',coverage='coverage.json',reason='finite logical cache model only; no CPU cycles, coherence, ordering or durability guarantee')
