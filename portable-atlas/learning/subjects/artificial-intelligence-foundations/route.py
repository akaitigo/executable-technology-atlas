# SPDX-License-Identifier: Apache-2.0
"""Author routing smoke: deterministic local dispatch, not independent AgentEval."""
import argparse
import json


def route(topic):
    if topic in ('bfs','astar','heuristic','reopen','tie','unreachable','invalid'):
        return dict(status='supported',runner='python3 verify.py',ui='index.html',reference='README.md')
    return dict(status='unsupported',reference='coverage.json',reason='This unit implements finite grid search only; no ML/LLM training.')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('topic')
    args = p.parse_args()
    print(json.dumps(route(args.topic),ensure_ascii=False))
