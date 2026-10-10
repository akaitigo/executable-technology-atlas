#!/usr/bin/env python3
"""Atlas: package existing saved bytes for the reader; does not run the model."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
status=json.loads((ROOT/'status.json').read_text());observation=status.get('observation')
run_text=(ROOT/observation).read_text() if observation else None
if run_text is not None:
    run=json.loads(run_text)
    if not run['collection_complete'] or run['errors']:raise SystemExit('Atlas: incomplete run cannot become reader evidence')
text=json.dumps({'project':'Atlas','run_text':run_text,'expected_text':(ROOT/'expected.json').read_text()},ensure_ascii=False,separators=(',',':'))
sha=hashlib.sha256(text.encode()).hexdigest()
(ROOT/'data.js').write_text('window.ATLAS_DATA_TEXT = '+json.dumps(text,ensure_ascii=False)+';\n')
p=ROOT/'lesson.js';s=p.read_text();s,count=re.subn(r"const DATA_SHA='[a-f0-9]{64}';","const DATA_SHA='%s';"%sha,s)
if count!=1:raise SystemExit('Atlas: reader pin missing or ambiguous')
p.write_text(s)
r={'project':'Atlas','observation':observation,'run_sha256':hashlib.sha256(run_text.encode()).hexdigest() if run_text else None,'expected_sha256':hashlib.sha256((ROOT/'expected.json').read_bytes()).hexdigest(),'payload_utf8_sha256':sha,'payload_digest_is_not_run_file_digest':True,'data_js_sha256':hashlib.sha256((ROOT/'data.js').read_bytes()).hexdigest(),'new_target_executions':0}
(ROOT/'records/bundle.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r))
