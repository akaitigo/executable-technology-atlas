"""No substitution or rename: bound-index compile plus tuple environment evaluation."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
FIXTURE=json.loads((ROOT/'fixture.json').read_text());TABLE=json.loads((ROOT/'oracle.json').read_text())
def compile_term(t,binders=()):
 k=t['kind']
 if k=='Int':return ('number',t['value'])
 if k=='Var':return ('bound',binders.index(t['name'])) if t['name'] in binders else ('free',t['name'])
 if k=='Lam':return ('lambda',compile_term(t['body'],(t['name'],)+binders))
 if k=='App':return ('apply',compile_term(t['fn'],binders),compile_term(t['arg'],binders))
 if k=='Add':return ('sum',compile_term(t['left'],binders),compile_term(t['right'],binders))
 raise AssertionError('not a valid oracle input')
def interpret(code,globals_,stack=()):
 tag=code[0]
 if tag=='number':return code[1]
 if tag=='free':return globals_[code[1]]
 if tag=='bound':return stack[code[1]]
 if tag=='lambda':return ('closure',code[1],stack,globals_)
 if tag=='sum':return interpret(code[1],globals_,stack)+interpret(code[2],globals_,stack)
 return invoke(interpret(code[1],globals_,stack),interpret(code[2],globals_,stack))
def invoke(closure,arg):
 assert closure[0]=='closure';return interpret(closure[1],closure[3],(arg,)+closure[2])
def run_code(t,env,args):
 value=interpret(compile_term(t),env)
 for arg in args:value=invoke(value,arg)
 return value
def environment_oracle(case):
 outer=case['environment'].copy();replacement=interpret(compile_term(case['replacement']),outer);bound=outer.copy();bound[case['target']]=replacement
 return run_code(case['term'],bound,case['arguments'])
def validate(raw):
 assert raw['fixture']==FIXTURE and [c['case'] for c in raw['cases']]==list(TABLE['expected']);normal=0
 for r,c in zip(raw['cases'],FIXTURE['cases']):
  x=TABLE['expected'][c['id']];assert r['input']==c
  assert r['status']==x['status'] and r['reason']==x['reason']
  if x['status']!='NORMAL':assert r['safe'] is None and r['naive'] is None;continue
  normal+=1;assert r['term_free']==x['term_free'] and r['replacement_free']==x['replacement_free']
  for mode in ['safe','naive']:
   for key in ['ast','free','value']:assert r[mode][key]==x[mode][key],(c['id'],mode,key)
   assert run_code(r[mode]['ast'],c['environment'],c['arguments'])==x[mode]['value']
  assert environment_oracle(c)==x['safe']['value']
  renames=[[e['old'],e['fresh']] for e in r['safe']['events'] if e['action']=='alpha-rename'];assert renames==x['renames']
  assert not any(e['action']=='alpha-rename' for e in r['naive']['events'])
  if c['id']=='same-binder':assert r['safe']['events']==r['naive']['events']==[dict(action='stop-binder',name='x')]
 return dict(cases=len(raw['cases']),environment_comparisons=normal,handwritten_free_sets=True,independent_bound_index_evaluation=True,general_type_safety_proved=False)
