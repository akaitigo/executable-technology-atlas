import json,hashlib,datetime,sys
from pathlib import Path
from oracle import check
P=Path(__file__).resolve().parent
def read(n):return json.loads((P/n).read_text())
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def core(raw,c,lit):
 assert json.loads(raw['input_json'])==c['input'] and raw['stderr']=='' and json.loads(raw['stdout'])==raw['result'];check(raw['result'],c['input'],lit)
 assert raw['exit']==(0 if raw['result']['status']=='OBSERVED' else 2 if raw['result']['status']=='INPUT_REFUSED' else 1)
 assert datetime.datetime.fromisoformat(raw['completed'])>=datetime.datetime.fromisoformat(raw['started'])
 for n,h in raw['source_sha256'].items():assert sha(P/n)==h,n
 if raw['result']['status']=='OBSERVED':
  a=raw['audit'];assert a['exit']==0 and a['stderr']=='' and json.loads(a['stdout'])==dict(status='passed',independent=True) and json.loads(a['stdin'])==dict(input=c['input'],result=raw['result'])
 else:assert raw['audit'] is None

def blank(o):assert o['status']=='未実行' and o['raw'] is None and not o['results_visible'] and not o['answer_visible'] and not o['answer_open'] and o['answer']=='' and o['counts']=='' and o['groups']=='' and o['ledger_table']==[] and o['bounds_table']==[] and o['states']==[] and o['ranges']==[] and o['undefined']==[] and o['points']==[]
def ui(o,c,lit):
 assert o['raw']['raw']==o['raw']['receipt'];raw=o['raw']['raw'];core(raw,c,lit);r=raw['result'];assert o['status']==r['status']
 if r['status']!='OBSERVED':assert not o['answer_visible'] and not o['answer_open'] and not o['results_visible'] and o['answer']=='' and o['states']==[] and o['ranges']==[] and o['ledger_table']==[] and o['bounds_table']==[];return
 assert o['answer_open'] and o['answer_visible'] and o['results_visible'];co=r['counts'];compact=lambda x:json.dumps(x,separators=(',',':'));null=lambda x:'null' if x is None else str(x);v=lambda x:'未定義/未観測' if x is None else str(x).lower() if isinstance(x,bool) else str(x)
 assert o['counts']=='N='+str(co['eligible'])+' / G='+str(co['good'])+' / B='+str(co['bad'])+' / U='+str(co['unknown'])+' / seen='+str(co['seen'])+' / excluded='+str(co['excluded'])+' / seen-only='+null(r['seenOnlySLI'])+' ('+r['seenOnlyVerdict']+') / 全台帳='+r['decision']
 assert o['ledger_table']==[[row['id'],v(row['eligible']),row['state'],v(row['arrived_tick'])] for row in r['rows']]
 def b(k,side):return r[k][side] if r[k] else None
 table=[['SLI',b('sliBounds','lower'),b('sliBounds','upper'),'全eligible分母' if co['eligible'] else 'NO_ELIGIBLE'],['bad',r['badBounds']['lower'],r['badBounds']['upper'],'未知を極端へ割当'],['allowed budget',r['allowedBudget'],r['allowedBudget'],'Fraction / 切上げなし'],['remaining',b('remainingBounds','lower'),b('remainingBounds','upper'),'下限worst / 上限best'],['burn',b('burnBounds','lower'),b('burnBounds','upper'),r['burnReason']]]
 assert o['bounds_table']==[[v(x) for x in row] for row in table]
 assert o['states']==[dict(id=row['id'],state=row['state'],eligible=str(row['eligible']).lower()) for row in r['rows']]
 assert o['ranges']==[dict(range=k,lower=r[k]['lower'],upper=r[k]['upper']) for k in ['sliBounds','remainingBounds','burnBounds'] if r[k]]
 assert o['undefined']==[k for k in ['sliBounds','remainingBounds','burnBounds'] if r[k] is None]
 assert o['points']==([r['target']] if r['sliBounds'] else [])
 for text in ['cutoff='+str(r['cutoff'])+', target='+r['target'],'N/G/B/U='+ '/'.join(str(co[k]) for k in ['eligible','good','bad','unknown']),'seen-only='+null(r['seenOnlySLI'])+' ('+r['seenOnlyVerdict']+')','全台帳='+r['decision'],'allowed='+r['allowedBudget'],'SLI='+compact(r['sliBounds']),'remaining='+compact(r['remainingBounds']),'burn='+compact(r['burnBounds'])+' ('+r['burnReason']+')','late IDs='+compact(r['lateIDs']),'実pipeline/本番保証/人の承認=UNCONFIRMED']+[k+' IDs='+compact(r['groups'][k]) for k in ['good','bad','unknown','excluded']]:assert text in o['answer'],text
 for k in ['good','bad','unknown','excluded']:assert k+' IDs='+compact(r['groups'][k]) in o['groups']

def browser(b):
 cs=read('fixture.json')+read('custom-oracle.json');lits=read('oracle.json');assert len(b['cases'])==24
 for o,c in zip(b['cases'],cs):assert o['id']==c['id'];ui(o,c,lits.get(c['id'],c.get('literal')))
 for k in ['prediction-verdict','prediction-bounds','input-json']:
  reset=b['reset'][k];assert reset['before']['answer_open'] and reset['before']['answer'];blank(reset['after']);idx=['prediction-verdict','prediction-bounds','input-json'].index(k)
  for i in range(3):assert reset['after']['inputs'][i]==(reset['new_value'] if i==idx else reset['before']['inputs'][i])
 blank(b['condition_reset']);assert b['condition_reset']['inputs']==['','','']
 r=b['invalid_json'];assert r['status']=='INPUT_REFUSED' and r['raw']['raw']['result']['reason']=='JSON' and not r['answer_visible'] and not r['results_visible'] and r['answer']==''
 f=b['communication_failure'];assert f['status']=='COMMUNICATION_FAILURE' and 'HTTP 503' in f['raw']['reason'] and not f['answer_visible'] and not f['results_visible'] and f['answer']=='' and f['points']==[]
 s=b['stale'];assert s['before_release']['raw']==s['after_release']['raw'] and s['before_release']['answer']==s['after_release']['answer'] and s['after_release']['ignored']=='古い結果の無視: 1';blank(s['edit_after_release']);assert s['edit_after_release']['ignored']=='古い結果の無視: 2';assert b['console']==[]
def verify():
 pointer=read('evidence/current.json');f=P/'evidence'/pointer['raw'];assert sha(f)==pointer['sha256'];report=json.loads(f.read_text());assert report['status']=='passed' and report['failures']==[] and len(report['attempts'])==24
 cs=read('fixture.json')+read('custom-oracle.json');lits=read('oracle.json')
 for a,c in zip(report['attempts'],cs):assert a['id']==c['id'];core(a['raw'],c,lits.get(c['id'],c.get('literal')))
 b=read('evidence/browser.json');browser(b)
 for n,t in b['documents'].items():assert (P/n).read_text()==t,n
 contract=read('evidence/contract-before-producer.json');assert contract['fixture_mtime_max_ns']<contract['producer_initial_mtime_ns']
 for n,d in contract['files'].items():assert sha(P/n)==d['sha256']
 for n,h in read('evidence/binding.json').items():assert sha(P/n)==h,n
 print(json.dumps(dict(status='passed',fixed=20,editable=4,ui=24,ledgerCompleteAssumed=True,approval='UNCONFIRMED',productionGuarantee='UNCONFIRMED',subject_complete=False)))
if __name__=='__main__':
 if sys.argv[1:]==['--record-binding']:(P/'evidence/binding.json').write_text(json.dumps({str(f.relative_to(P)):sha(f) for f in P.rglob('*') if f.is_file() and str(f.relative_to(P))!='evidence/binding.json'},indent=2)+'\n')
 else:verify()
