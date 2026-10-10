import argparse
import json
from model import experiment
p = argparse.ArgumentParser()
p.add_argument('--phase', choices=['initial','overlap','revoked'], default='overlap')
p.add_argument('--version', choices=['v1','v2'], default='v1')
p.add_argument('--now', type=int, default=100)
p.add_argument('--fault', choices=['none','tamper','unknown','input'], default='none')
a = p.parse_args()
print(json.dumps(experiment(a.phase, a.version, a.now, a.fault), ensure_ascii=False, indent=2))
