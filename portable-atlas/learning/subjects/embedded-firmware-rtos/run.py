import argparse,json
from model import SCHEDULES,experiment
p=argparse.ArgumentParser();p.add_argument('--schedule',choices=SCHEDULES,default='preempt-main');p.add_argument('--mode',choices=['naive','critical'],default='naive');p.add_argument('--hold',type=int,default=3);p.add_argument('--arrival',type=int,default=1);p.add_argument('--deadline',type=int,default=3);a=p.parse_args()
print(json.dumps(experiment(a.schedule,a.mode,a.hold,a.arrival,a.deadline),ensure_ascii=False,indent=2))
