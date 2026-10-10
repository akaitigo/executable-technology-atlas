"""Explicitly import actual IAB DOM/event observation; normal mode reads current raw only."""
import json,hashlib,datetime,uuid,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--record',action='store_true');a.add_argument('--input');args=a.parse_args()
 if args.record:
  if not args.input:a.error('--record requires actual IAB input file')
  source=Path(args.input);data=json.loads(source.read_text());raw=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),command='python3 -B record.py --record --input owned-IAB-capture.json',observation_origin='actual new owned Codex IAB tabs; native DOM and history actions',input_capture_sha256=sha(source),source_sha256={n:sha(ROOT/n) for n in ['fixture.json','oracle.json','EXPECTATIONS.md','app.js','index.html','record.py']},fixture=json.loads((ROOT/'fixture.json').read_text()),browser=data)
  name='run-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]+'.json'
  with (ROOT/'evidence'/name).open('x') as f:json.dump(raw,f,ensure_ascii=False,indent=2);f.write('\n')
  if not data.get('unexpected_execution_failure'):(ROOT/'evidence/current.json').write_text(json.dumps(dict(raw=name,sha256=sha(ROOT/'evidence'/name)),indent=2)+'\n')
  print(name)
 else:
  p=json.loads((ROOT/'evidence/current.json').read_text());print((ROOT/'evidence'/p['raw']).read_text())
