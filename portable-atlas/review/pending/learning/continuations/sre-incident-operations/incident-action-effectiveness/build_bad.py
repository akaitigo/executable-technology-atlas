import json,sys
VERSION='bad'
def handle(value,deadline):
 return dict(status='SUCCESS',output=value+1,logical_ticks=1)
if __name__=='__main__':
 try:
  x=json.loads(sys.stdin.read());assert isinstance(x,dict) and set(x)=={'value','deadline_ticks'};assert type(x['value'])==int and 0<=x['value']<=3 and type(x['deadline_ticks'])==int and 0<=x['deadline_ticks']<=3;print(json.dumps(handle(x['value'],x['deadline_ticks'])))
 except Exception:print(json.dumps(dict(status='INPUT_REFUSED')));sys.exit(2)
