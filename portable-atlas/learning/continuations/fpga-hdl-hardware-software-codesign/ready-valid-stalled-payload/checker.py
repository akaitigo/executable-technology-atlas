import copy,itertools,json,sys
sys.dont_write_bytecode=True
from runner import ROOT,SOURCES,collect,digest,snapshot
from oracle import expected
from evaluator import model
def verify(rows):
 for row in rows:
  p=row['run'];assert p['result']==row['expected'],row['id'];assert p['exit']==(2 if row['expected']['status']=='input_refusal' else 0) and not p['stderr'];assert json.loads(p['stdout'])==p['result']
  if row['expected']['status']=='observed':assert expected(json.loads(row['input_json']))==row['expected']
def main():
 before=snapshot();rows=collect()['rows'];verify(rows);count=0
 for n in range(5):
  for bits in itertools.product([0,1],repeat=n):
   for data in range(256):
    for valid in [0,1]:
     x={'data':data,'ready':list(bits),'valid':valid};oracle=expected(x)
     for mode in ['normal','advance_on_stall','ignore_ready']:assert model(x,mode)==oracle[mode]
     count+=1
 caught=[]
 for name,mode,field,val in [('post-edge-capture','normal','captured',[18]),('advance-hidden','advance_on_stall','captured',[17]),('ready-required','ignore_ready','captured',[17])]:
  mutant=copy.deepcopy(rows);mutant[0]['run']['result'][mode][field]=val
  try:verify(mutant)
  except AssertionError:caught.append(name)
  else:raise AssertionError('mutant survived')
 rawfile=ROOT/'observation-data.js'
 if rawfile.exists():
  raw=json.loads(rawfile.read_text().split('=',1)[1].rstrip(';\n'));verify(raw['rows']);assert raw['source_digests']=={n:digest(ROOT/n) for n in SOURCES};d=ROOT/'observations'/raw['run_id'];assert json.loads((d/'raw.json').read_text())==raw;idx=json.loads((d/'artifact-index.json').read_text());assert 'artifact-index.json' not in idx['files'];assert all(digest(d/n)==h for n,h in idx['files'].items())
 assert before==snapshot();print(json.dumps({'literal_cases':15,'closed_form_comparisons':count,'mutants_rejected':caught,'read_only':True}));return 0
if __name__=='__main__':sys.exit(main())
