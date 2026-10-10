# SPDX-License-Identifier: Apache-2.0
import json,sys

def route(topic):
    if topic in ('bpsk','iq','phase','pilot','ber','fixed-noise','trace'):
        return dict(status='supported',runner='python3 verify.py',ui='index.html',reference='README.md')
    return dict(status='unsupported',reference='coverage.json',reason='Finite BPSK calculation only; no RF transmit/receive, SDR hardware, standards modem or live channel')
if __name__=='__main__':print(json.dumps(route(sys.argv[1] if len(sys.argv)>1 else ''),ensure_ascii=False))
