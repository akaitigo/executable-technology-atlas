# SPDX-License-Identifier: Apache-2.0
def route(topic):
 if topic in ['priority-inheritance','blocking','priority-inversion','deadline']:return dict(status='supported',runner='python3 verify.py',ui='index.html',guide='README.md')
 return dict(status='unsupported',coverage='coverage.json',reason='finite 1CPU/1lock/tick model; no actual OS, WCET or safety certification')
