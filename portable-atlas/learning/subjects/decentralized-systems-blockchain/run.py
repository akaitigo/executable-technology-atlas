import argparse,json
from model import CASES,experiment
p=argparse.ArgumentParser();p.add_argument('--case',choices=CASES,default='normal');p.add_argument('--amount',type=int,default=10);a=p.parse_args()
print(json.dumps(experiment(a.case,a.amount),ensure_ascii=False,indent=2))
