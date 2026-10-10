"""Connect verified saved JSON to a reader. No producer import/execution."""
import hashlib
import json
from pathlib import Path
from verify import check

ROOT=Path(__file__).resolve().parent


def main():
    result=ROOT/'observations/result.json'
    raw=result.read_bytes();data=json.loads(raw)
    checked=check(data)
    verification=json.loads((ROOT/'observations/verification.json').read_text())
    digest=hashlib.sha256(raw).hexdigest()
    assert verification['passed'] is True and verification['result_sha256']==digest
    reader=dict(schema='atlas-root-boundaries-reader-v1',run_id=data['run']['run_id'],
                observed_at_utc=data['run']['observed_at_utc'],result_sha256=digest,
                fixture=data['fixture'],values=data['values'])
    before=ROOT/'history/before-reader-connection';before.mkdir(parents=True,exist_ok=False)
    for filename,var in [('reader-data.js','ROOT_BOUNDARY_DATA'),('reader-expectations.js','ROOT_BOUNDARY_EXPECTED')]:
        path=ROOT/filename
        (before/filename).write_bytes(path.read_bytes())
        path.write_text('window.'+var+' = '+json.dumps(reader,ensure_ascii=False,indent=2)+';\n')
    report=dict(passed=True,result_sha256=digest,checked=checked,
                expected_role='exact pin of saved data, not independent mathematical oracle',
                independent_oracle='hand-oracle.json locked before producer; separately reviewed',
                sources={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
                         ['connect-reader.py','verify.py','reader-data.js','reader-expectations.js','hand-oracle.json','contract-lock.json']},
                model_executions=0)
    (ROOT/'observations/reader-connection.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
