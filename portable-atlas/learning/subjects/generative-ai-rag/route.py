# SPDX-License-Identifier: Apache-2.0
"""Author routing smoke; not independent AgentEval."""
import argparse
import json


def route(topic):
    if topic in ('retrieval','context','citation','grounding','missing-context','instruction-boundary','invalid'):
        return dict(status='supported',runner='python3 verify.py',ui='index.html',reference='README.md')
    return dict(status='unsupported',reference='coverage.json',reason='Fixed lexical retrieval and authored fixtures only; no generative model, embeddings, API or production RAG')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('topic');args=p.parse_args()
    print(json.dumps(route(args.topic)))
