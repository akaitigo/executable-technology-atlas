# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path
HAND=json.loads((Path(__file__).parent/'hand-oracle.json').read_text());FIXTURES={x['id']:x for x in HAND['fixtures']}
def configs():return [dict(fixture=f,mode=m,h=h) for f in FIXTURES for m in ['delayed','zero-delay','instant'] for h in [.5,1.]]
def valid(c):return type(c) is dict and set(c)=={'fixture','mode','h'} and type(c['fixture']) is str and c['fixture'] in FIXTURES and type(c['mode']) is str and c['mode'] in ['delayed','zero-delay','instant'] and type(c['h']) in [int,float] and c['h'] in [.5,1.]
