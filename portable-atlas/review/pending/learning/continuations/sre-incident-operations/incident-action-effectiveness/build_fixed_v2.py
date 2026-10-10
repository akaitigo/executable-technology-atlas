import json,sys
VERSION='fixed-v2'
def handle(value,deadline):
 if deadline >= 2:return dict(status='SUCCESS',output=value*2,logical_ticks=2)
 return dict(status='TIMEOUT',output=None,logical_ticks=deadline)
if __name__=='__main__':
 try:
  x=json.loads(sys.stdin.read());assert isinstance(x,dict) and set(x)=={'value','deadline_ticks'};assert type(x['value'])==int and 0<=x['value']<=3 and type(x['deadline_ticks'])==int and 0<=x['deadline_ticks']<=3;print(json.dumps(handle(x['value'],x['deadline_ticks'])))
 except Exception:print(json.dumps(dict(status='INPUT_REFUSED')));sys.exit(2)
