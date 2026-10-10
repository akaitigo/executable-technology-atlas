"""Atlas: connect an already verified saved result; never call the receiver."""
import argparse
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('run'); args = parser.parse_args()
    directory = (ROOT/args.run).resolve(); assert ROOT/'observations' in directory.parents
    report = json.loads((directory/'report.json').read_text()); result = json.loads((directory/'result.json').read_text())
    verification = json.loads((directory/'verification.json').read_text())
    assert report['status']=='observed' and report['child_reaped'] and report['exit_code']==0
    assert report['result_sha256']==sha(directory/'result.json')
    assert verification['passed'] and verification['model_rerun'] is False and verification['run']==args.run
    assert verification['source_sha256']==sha(ROOT/'verify.py') and len(verification['mutation_refusals'])==16
    fixture=json.loads((ROOT/'fixtures.json').read_text())
    assert result['fixture_sha256']==sha(ROOT/'fixtures.json')
    assert result['comparison_truth_sha256']==sha(ROOT/'comparison-truth.json')
    data={'title':'Atlas saved telecom phase reader data','run_id':directory.name,
          'result_sha256':sha(directory/'result.json'),'fixture':fixture,'result':result}
    text=json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False)
    (ROOT/'reader-data.js').write_text('window.ATLAS_PHASE_DATA = '+text+';\n')
    (ROOT/'reader-expectations.js').write_text('window.ATLAS_PHASE_EXPECTED = '+text+';\n')
    connection={'title':'Atlas saved phase reader connection','run':args.run,'run_id':directory.name,
        'result_sha256':data['result_sha256'],'observed_at_utc':result['observed_at_utc'],'model_rerun':False,
        'source_sha256':{n:sha(ROOT/n) for n in ['connect-reader.py','verify.py','fixtures.json','reader-data.js','reader-expectations.js']}}
    (ROOT/'observations/reader-connection.json').write_text(json.dumps(connection,indent=2)+'\n')
    print(json.dumps({'connected':True,'run':args.run,'model_rerun':False}))


if __name__=='__main__':main()
