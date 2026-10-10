# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path
HAND=json.loads((Path(__file__).parent/'hand-oracle.json').read_text())
FIXTURES={x['id']:x['operations'] for x in HAND['fixtures']}
def configs():
 return [dict(fixture=f,policy=p,mode=m) for f in FIXTURES for p in ['fixed','doubling'] for m in ['normal','delete-whole-bucket']]
def valid(c):
 return type(c) is dict and set(c)=={'fixture','policy','mode'} and type(c['fixture']) is str and c['fixture'] in FIXTURES and type(c['policy']) is str and c['policy'] in ['fixed','doubling'] and type(c['mode']) is str and c['mode'] in ['normal','delete-whole-bucket']
