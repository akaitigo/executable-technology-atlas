# SPDX-License-Identifier: Apache-2.0
def route(topic):
    if topic in ['deadlock','retry','cycle','safety','termination','two-lock']:
        return dict(status='supported',runner='python3 verify.py',ui='index.html',guide='README.md')
    return dict(status='unsupported',reason='finite model only; no TLC, OS threads, fairness theorem or general proof',coverage='coverage.json')
