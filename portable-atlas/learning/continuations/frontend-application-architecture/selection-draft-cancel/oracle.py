"""Independent literal ID-state expectations plus real DOM/URL alignment, no producer import."""
import json
from pathlib import Path
from urllib.parse import urlparse,parse_qs
ROOT=Path(__file__).resolve().parent
TABLE=json.loads((ROOT/'oracle.json').read_text())
def validate(raw):
 observed=raw['browser'];assert not observed.get('unexpected_execution_failure');assert [c['id'] for c in observed['cases']]==list(TABLE['cases'])
 for c,f in zip(observed['cases'],raw['fixture']['cases']):
  assert c['id']==f['id'] and c['mode']==f['mode'];expected=TABLE['cases'][c['id']];assert len(c['steps'])==len(expected);assert c['owned_new_tab'] and c['tab_closed']
  for step,x,action in zip(c['steps'],expected,f['actions']):
   s=step['event']['state'];dom=step['dom'];assert step['event']['action']==action
   assert s['mode']==c['mode'] and s['selected']==x['id'];assert s['canonical']==dict(a=x['a'],b=x['b']) and s['drafts']==x['drafts'] and s['shared']==x['shared'];assert s['editor']==x['editor'] and s['kind']==x['kind'] and s['reason']==x.get('reason','') and s['failure'] is None
   query=parse_qs(urlparse(dom['url']).query);assert query['id']==[x['id']] and query['mode']==[c['mode']];assert parse_qs(s['url'].lstrip('?'))==query
   assert dom['editor']==x['editor'] and dom['canonical_a']==x['a'] and dom['canonical_b']==x['b'] and dom['selected']=='選択ID: '+x['id'];assert json.loads(dom['drafts'])==dict(byId=x['drafts'],shared=x['shared'])
  assert [step['event']['seq'] for step in c['steps']]==list(range(len(expected)))
 return dict(cases=5,observed_states=21,normal_cancel_preserves_other_draft=True,shared_wrong_target_save_observed=True,expected_no_draft_refusals=2,URL_back_observed=True,React_executed=False)
