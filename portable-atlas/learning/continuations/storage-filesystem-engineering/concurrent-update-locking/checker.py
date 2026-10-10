"""Focused saved observation checker. No subprocess/file mutation without explicit flag."""
import json,hashlib,argparse,re
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from route import route
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def binding():return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='binding.json' and '__pycache__' not in p.parts}
def verify():
 r=json.loads((ROOT/'evidence/raw.json').read_text());o=json.loads((ROOT/'oracle.json').read_text());assert len(r['cases'])==len(o['cases'])==3
 pids=[]
 for c,expected in zip(r['cases'],o['cases']):
  assert c['id']==expected['id'] and c['finalbytes']==expected['finalbytes'] and c['visible']==expected['visible']
  ev=c['events'];middle=ev[2:-2];assert [(e['writer'],e['event']) for e in middle]==[(n,event) for n,op,event in expected['schedule']]
  assert [e['value'] for e in ev if e['event']=='read']==expected['reads']
  assert [e['value'] for e in ev if e['event']=='write']==[v+1 for v in expected['reads']]
  assert all(e.get('bytes')==str(e['value'])+'\n' for e in ev if e['event'] in ('read','write'))
  assert len({ev[0]['pid'],ev[1]['pid']})==2
  for n in ('A','B'):
   child=c['children'][n];pids.append(child['pid']);assert child['exit_code']==0 and child['reaped'] and child['stderr']==''
   lines=[json.loads(line) for line in c['raw_stdout'][n].splitlines()];assert lines==[e for e in ev if e['writer']==n] and all(e['pid']==child['pid'] for e in lines)
  assert c['temp_removed']
  lock=[e for e in ev if 'lock_inode' in e];assert not lock or len({e['lock_inode'] for e in lock})==1
  if c['id']!='replace-only':
   owner=None
   for e in ev:
    if e['event']=='acquired':assert owner is None;owner=e['writer']
    if e['event']=='would_block':assert owner is not None and owner!=e['writer']
    if e['event'] in ('read','write','rename','abort_before_replace'):assert owner==e['writer']
    if e['event']=='released':assert owner==e['writer'];owner=None
   assert owner is None
 t=r['timeout'];assert t['event']=='controller_timeout' and t['child']['reaped'] and t['child']['exit_code']!=0 and t['temp_removed'];assert r['durability_proven'] is False
 for n,h in r['source_sha256'].items():assert sha(ROOT/n)==h,('source drift',n)
 # Reject plausible false claims using fixed expected states, independent of worker.
 assert o['cases'][0]['finalbytes']!='2\n' and o['cases'][1]['reads']!=[0,0] and o['cases'][2]['finalbytes']!='2\n'
 for topic in ('locking','verify','timeline','sources'):assert route(topic)['status']=='supported' and (ROOT/route(topic)['target']).exists()
 for topic in ('power-loss','nfs','linux-kernel','speedup','external-path'):assert route(topic)['status']=='unsupported'
 links=0
 for f in [ROOT/'README.md',ROOT/'SOURCES.md',ROOT/'skills/atlas-storage-locking/SKILL.md',ROOT/'index.html']:
  text=f.read_text();refs=re.findall(r'\]\(([^)]+)\)',text) if f.suffix=='.md' else re.findall(r'(?:href|src)="([^"]+)"',text)
  for ref in refs:
   if ref.startswith(('http','#')):continue
   parsed=urlsplit(ref);assert (f.parent/parsed.path).exists(),(f.name,ref)
   for n in parse_qs(parsed.query).get('file',[]):assert (ROOT/n).is_file(),n
   links+=1
 qa=json.loads((ROOT/'evidence/ui-qa.json').read_text());assert qa['status']=='passed' and qa['raw_sha256']==sha(ROOT/'evidence/raw.json') and qa['owned_cleanup'] is True
 assert json.loads((ROOT/'evidence/binding.json').read_text())==binding(),'artifact binding drift'
 return dict(status='passed',actual_two_writer_cases=3,owned_writer_processes=6,timeout_process_reaped=True,independent_schedule_bytes_reads=True,falsified_claims_rejected=3,route_checks='4 supported / 5 unsupported',local_links=links,subject_complete=False,durability_proven=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--record-binding',action='store_true');a=p.parse_args()
 if a.record_binding:(ROOT/'evidence/binding.json').write_text(json.dumps(binding(),indent=2)+'\n')
 try:print(json.dumps(verify(),ensure_ascii=False,indent=2))
 except (AssertionError,ValueError,KeyError,FileNotFoundError) as e:print(json.dumps(dict(status='failed',reason=str(e))));raise SystemExit(1)
