"""Connect an already saved and verified result; never calculates guest steps."""
import argparse
import hashlib
import json
from pathlib import Path
from verify import check, sha

ROOT=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--result',type=Path,required=True)
    parser.add_argument('--verification',type=Path,required=True);args=parser.parse_args()
    result=json.loads(args.result.read_text());verification=json.loads(args.verification.read_text())
    assert verification['passed'] is True and verification['result_sha256']==sha(args.result)
    assert verification['verify_source_sha256']==sha(ROOT/'verify.py')
    assert verification['run_id']==result['run']['run_id']
    check(result)
    data=dict(schema='atlas-device-snapshot-reader-v1',run_id=result['run']['run_id'],
              observed_at_utc=result['run']['observed_at_utc'],result_sha256=sha(args.result),
              fixture=result['fixture'],values=result['values'])
    snapshots=ROOT/'history/before-reader-connection';snapshots.mkdir(parents=True,exist_ok=True)
    for filename,variable in [('reader-data.js','DeviceSnapshotData'),('reader-expectations.js','DeviceSnapshotExpected')]:
        target=ROOT/filename;old=snapshots/filename
        assert not old.exists(),'connection already recorded; do not overwrite'
        old.write_bytes(target.read_bytes())
        target.write_text('globalThis.'+variable+' = '+json.dumps(data,ensure_ascii=False,sort_keys=True)+';\n')
    record=dict(result_sha256=sha(args.result),run_id=data['run_id'],verify_source_sha256=sha(ROOT/'verify.py'),
                connection_source_sha256=sha(Path(__file__)),data_sha256=sha(ROOT/'reader-data.js'),
                expected_sha256=sha(ROOT/'reader-expectations.js'),expected_role='exact saved-value pin, not independent mathematical oracle',
                producer_executions=0)
    (ROOT/'observations/reader-connection.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(record,ensure_ascii=False))


if __name__=='__main__':main()
