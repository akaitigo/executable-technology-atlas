import argparse
import json
from pathlib import Path
from model import simulate
ROOT = Path(__file__).resolve().parent

def run(data):
    try:
        return simulate(data)
    except ValueError as e:
        return {'status': 'rejected', 'error': str(e), 'traces': {}}

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='状態遷移モデル。通常実行は原票を書かない')
    p.add_argument('--input-json')
    a = p.parse_args()
    try:
        data = json.loads(a.input_json) if a.input_json is not None else json.loads((ROOT/'cases.json').read_text())[0]['input']
        out = run(data)
    except json.JSONDecodeError:
        out = {'status': 'rejected', 'error': 'invalid JSON', 'traces': {}}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    raise SystemExit(2 if out['status'] == 'rejected' else 0)
