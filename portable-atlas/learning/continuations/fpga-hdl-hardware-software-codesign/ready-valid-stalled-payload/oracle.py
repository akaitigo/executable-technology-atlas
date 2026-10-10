"""Closed-form oracle: first ready index, independent of iterative evaluator."""
def expected(x):
 first=next((i for i,r in enumerate(x['ready']) if r==1),None);out={}
 for mode in ['normal','advance_on_stall','ignore_ready']:
  ticks=[]
  for i,r in enumerate(x['ready']):
   v=int(bool(x['valid']) and (first is None or i<=first));offset=min(i,first) if first is not None else i
   d=(x['data']+offset)%256 if mode=='advance_on_stall' and x['valid'] else x['data']
   cap=bool(v and (r==1 or mode=='ignore_ready'));post=int(bool(x['valid']) and (first is None or i<first));pd=(d+1)%256 if mode=='advance_on_stall' and v and r==0 else d
   ticks.append({'tick':i,'valid':v,'ready':r,'data':d,'capture':cap,'captured':d if cap else None,'after_valid':post,'after_data':pd})
  out[mode]={'ticks':ticks,'captured':[t['captured'] for t in ticks if t['capture']]}
 return {'status':'observed','input':x,**out}
