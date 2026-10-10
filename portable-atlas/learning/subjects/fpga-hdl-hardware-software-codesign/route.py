"""Finite skill route. Pure/read-only and deterministic."""
import argparse, json
ROUTES = {'counter': 'runner.py', 'verify': 'checker.py', 'waveform': 'index.html', 'sources': 'SOURCES.md'}
def route(topic):
    return {'status': 'supported', 'target': ROUTES[topic]} if topic in ROUTES else {'status': 'unsupported', 'reason': '今回未教材: synthesis/timing/CDC/AXI/HLS/実機等はCOVERAGE.md参照', 'target': 'COVERAGE.md'}
if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('topic'); a = p.parse_args()
    r = route(a.topic); print(json.dumps(r, ensure_ascii=False)); raise SystemExit(0 if r['status']=='supported' else 2)
