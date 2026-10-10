import argparse,json
from model import experiment
p=argparse.ArgumentParser()
p.add_argument('--case',choices=['normal','late','duplicate','invalid','boundary','outside','other-user'],default='late')
p.add_argument('--mode',choices=['arrival','event-time'],default='event-time')
p.add_argument('--window',type=int,default=30)
p.add_argument('--threshold',type=int,default=3)
a=p.parse_args()
print(json.dumps(experiment(a.case,a.mode,a.window,a.threshold),ensure_ascii=False,indent=2))
