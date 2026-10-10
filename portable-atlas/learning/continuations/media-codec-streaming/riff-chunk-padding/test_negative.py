#!/usr/bin/env python3
import hashlib,json,pathlib,shutil,sys,tempfile
sys.dont_write_bytecode=True
import checker
ROOT=pathlib.Path(__file__).resolve().parent
def fp():return {str(p):(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in ROOT.rglob('*') if p.is_file()}
def main():
 run=ROOT/(ROOT/'CURRENT').read_text().strip();before=fp();checker.check(run);assert before==fp();out=[{'test':'read-only SHA256+mtime_ns','passed':True}]
 for kind in ['omit-pad-next','wrong-pcm','declared-as-actual','false-refusal-success','wrong-wave-complete','wrong-bug-size']:
  with tempfile.TemporaryDirectory(prefix='riff-negative-') as td:
   temp=pathlib.Path(td)/'run';shutil.copytree(run,temp);d=json.loads((temp/'result.json').read_text());c=d['cases'][1];o=c['observation']
   if kind=='omit-pad-next':o['strict']['chunks'][1]['nextOffset']=47;o['strict']['chunks'][1]['padBytes']=0
   if kind=='wrong-pcm':o['strict']['pcmHex']='000018fcff7f';o['strict']['samples']=[0,-1000,32767]
   if kind=='declared-as-actual':c=d['cases'][4];c['observation']['strict']['chunks'][2]['actualAvailable']=10
   if kind=='false-refusal-success':c=d['cases'][5];c['exitCode']=0;c['observation']['strict']['accepted']=True;c['observation']['strict']['reason']=None
   if kind=='wrong-wave-complete':c=d['cases'][5];c['observation']['wave']['completeDeclaredFrames']=True
   if kind=='wrong-bug-size':o['omitPaddingBug']['chunks'][2]['declaredSize']=6
   for rec in d['cases']:
    rec['stdout']=json.dumps(rec['observation'])+'\n';(temp/rec['id']/'stdout.json').write_text(rec['stdout'])
   (temp/'result.json').write_text(json.dumps(d));(temp/'stdout.json').write_text(json.dumps(d)+'\n')
   art={str(p.relative_to(temp)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in temp.rglob('*') if p.is_file() and p.name!='artifacts.json'};(temp/'artifacts.json').write_text(json.dumps(art))
   try:checker.check(temp)
   except AssertionError as e:out.append({'test':kind,'passed':True,'rawDerivedHashesConsistent':True,'oracleRejection':str(e)})
   else:raise AssertionError('accepted '+kind)
 assert before==fp();print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
