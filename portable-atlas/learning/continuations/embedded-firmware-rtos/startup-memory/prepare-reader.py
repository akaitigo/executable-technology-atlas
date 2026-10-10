"""Atlas: connect an existing verified calculation to the reader; no model execution."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run');args=p.parse_args()
    run=(ROOT/args.run).resolve();assert ROOT/'observations' in run.parents
    report=json.loads((run/'report.json').read_text());result=json.loads((run/'result.json').read_text())
    assert report['status']=='observed' and report['child_reaped'] and report['exit_code']==0
    assert report['result_sha256']==sha(run/'result.json')
    bundle={'title':'Atlas startup memory saved calculation','run_id':run.name,'result_sha256':sha(run/'result.json'),'result_path':str((run/'result.json').relative_to(ROOT)),'fixture_sha256':sha(ROOT/'fixtures.json'),'fixtures':json.loads((ROOT/'fixtures.json').read_text()),'result':result}
    for name,variable in [('reader-data.js','AtlasStartupData'),('reader-expectations.js','AtlasStartupExpected')]:
        (ROOT/name).write_text('/* Atlas: fixed saved calculation, not a new execution. */\nglobalThis.'+variable+' = '+json.dumps(bundle,ensure_ascii=False,indent=2)+';\n')
    receipt={'title':'Atlas saved calculation connection','run':args.run,'model_rerun':False,'source_sha256':sha(Path(__file__)),'result_sha256':sha(run/'result.json'),'fixture_sha256':sha(ROOT/'fixtures.json'),'files':{name:sha(ROOT/name) for name in ['reader-data.js','reader-expectations.js']}}
    (ROOT/'observations/reader-connection.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(receipt))
if __name__=='__main__':main()
