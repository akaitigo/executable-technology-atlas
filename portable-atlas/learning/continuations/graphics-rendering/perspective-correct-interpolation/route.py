# SPDX-License-Identifier: Apache-2.0
def route(topic):
    if topic in ['perspective','uv','barycentric','noperspective','ray-oracle','png']:
        return dict(status='supported',runner='python3 verify.py',ui='index.html',guide='README.md')
    return dict(status='unsupported',reason='finite CPU attribute interpolation only; no GPU, clipping, filtering or color-management guarantee',coverage='coverage.json')
