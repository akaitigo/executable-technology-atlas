#!/usr/bin/env python3
import json,sys
from fractions import Fraction
def rational(f):return [f.numerator,f.denominator]
def main():
 events=json.load(open(sys.argv[1]));out={'input':events,'slo':[9,10],'threshold':[2,1],'windows':None,'and':None,'shortOnly':None,'reason':None};seen=set()
 def reject(reason):out['reason']=reason;print(json.dumps(out));return 2
 if type(events) is not list:return reject('invalid-events-type')
 for e in events:
  if type(e) is not dict or set(e)!=set(['id','tick','status']):return reject('invalid-event-shape')
  if type(e['id']) is not int or e['id']<0:return reject('invalid-id')
  if e['id'] in seen:return reject('duplicate-id:'+str(e['id']))
  seen.add(e['id'])
  if type(e['tick']) is not int:return reject('invalid-tick:'+type(e['tick']).__name__)
  if e['status'] not in ['good','bad']:return reject('unknown-status:'+str(e['status']))
 windows={}
 for name,lo,hi in [('long',0,100),('short',90,100)]:
  included=[e for e in events if lo<=e['tick']<hi];failed=[e['id'] for e in included if e['status']=='bad'];burn=Fraction(len(failed),len(included))/Fraction(1,10) if included else None
  windows[name]={'range':[lo,hi],'eventIds':[e['id'] for e in included],'failedIds':failed,'denominator':len(included),'failures':len(failed),'errorRate':rational(Fraction(len(failed),len(included))) if included else None,'burn':rational(burn) if burn is not None else None,'burnText':str(burn) if burn is not None else '未定義','overThreshold':burn>=Fraction(2,1) if burn is not None else None}
 out['windows']=windows;empty=[n for n,w in windows.items() if w['denominator']==0]
 if empty:return reject('empty-window:'+','.join(empty))
 out['and']=windows['long']['overThreshold'] and windows['short']['overThreshold'];out['shortOnly']=windows['short']['overThreshold'];print(json.dumps(out));return 0
if __name__=='__main__':sys.exit(main())
