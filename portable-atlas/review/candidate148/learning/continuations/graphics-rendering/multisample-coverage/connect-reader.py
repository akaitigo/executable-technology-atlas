"""Atlas: bind verified saved JSON to the reader; no renderer or GPU execution."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('run'); args = parser.parse_args()
    directory = (ROOT/args.run).resolve(); assert directory.parent == ROOT/'observations'
    report = json.loads((directory/'report.json').read_text())
    result = json.loads((directory/'result.json').read_text())
    verification = json.loads((directory/'verification.json').read_text())
    assert report['status'] == 'observed' and report['exit_code'] == 0 and report['child_reaped']
    assert sha(directory/'result.json') == report['result_sha256'] == verification['result_sha256']
    assert verification['passed'] is True and verification['model_rerun'] is False
    assert verification['run'] == args.run and verification['verify_source_sha256'] == sha(ROOT/'verify.py')
    assert len(verification['alterations_detected']) == 18
    assert result['fixture_sha256'] == sha(ROOT/'fixtures.json')
    history = ROOT/'history/before-reader-connection'; history.mkdir(parents=True,exist_ok=False)
    for name in ['reader-data.js','reader-expectations.js','status.json']:
        (history/name).write_bytes((ROOT/name).read_bytes())
    data = {'title':'Atlas saved multisample data','schema':1,'run_id':directory.name,
            'observed_at_utc':result['observed_at_utc'],'result_sha256':sha(directory/'result.json'),
            'fixture':json.loads((ROOT/'fixtures.json').read_text()),'result':result}
    body=json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False)
    (ROOT/'reader-data.js').write_text('globalThis.ATLAS_DATA = '+body+';\n')
    (ROOT/'reader-expectations.js').write_text('// Atlas: integrity copy, not an independent oracle.\nglobalThis.ATLAS_EXPECTED = '+body+';\n')
    connection={'title':'Atlas saved multisample reader connection','run':args.run,'run_id':directory.name,
                'result_sha256':data['result_sha256'],'observed_at_utc':data['observed_at_utc'],
                'model_rerun':False,'expectations_are_saved_data_copy':True,
                'sources':{n:sha(ROOT/n) for n in ['connect-reader.py','verify.py','fixtures.json','reader-data.js','reader-expectations.js']}}
    (ROOT/'observations/reader-connection.json').write_text(json.dumps(connection,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'connected':True,'run':args.run,'model_rerun':False}))


if __name__ == '__main__':
    main()
