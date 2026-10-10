# SPDX-License-Identifier: Apache-2.0
"""Deterministic author routing smoke, not independent AgentEval."""
import argparse
import json


def route(topic):
    if topic in ('state-machine','tool-allowlist','budget','loop','end','error','result-boundary','audit'):
        return dict(status='supported',runner='python3 verify.py',ui='index.html',reference='README.md')
    return dict(status='unsupported',reference='coverage.json',reason='Fixed dummy-tool plans only; no LLM reasoning, autonomous planning, external tools or real agent platform')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('topic');args=p.parse_args();print(json.dumps(route(args.topic)))
