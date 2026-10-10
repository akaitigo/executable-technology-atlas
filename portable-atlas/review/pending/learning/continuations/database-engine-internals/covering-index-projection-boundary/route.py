import argparse,json,sys
from pathlib import Path
from execute import execute
P=Path(__file__).resolve().parent
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('case');a.add_argument('--input-json',default='');args=a.parse_args();cases=json.loads((P/'fixture.json').read_text());c=next((v for v in cases if v['id']==args.case),None)
 if c is None:print(json.dumps({'status':'INPUT_REFUSED','reason':'UNKNOWN_CASE'}));sys.exit(2)
 raw=execute(args.input_json or json.dumps(c['input']),c.get('inject_failure',False));print(json.dumps(raw));sys.exit(raw['exit'])
