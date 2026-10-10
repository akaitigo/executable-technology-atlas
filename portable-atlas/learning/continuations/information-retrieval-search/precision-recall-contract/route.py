# SPDX-License-Identifier: Apache-2.0
def route(topic):
 if topic in ['precision','recall','labels','boolean','undefined','retrieval-quality']:
    return dict(status='supported',runner='python3 verify.py',ui='index.html',guide='README.md')
 return dict(status='unsupported',coverage='coverage.json',reason='finite synthetic unranked sets; no ranking, user study, product search or performance guarantee')
