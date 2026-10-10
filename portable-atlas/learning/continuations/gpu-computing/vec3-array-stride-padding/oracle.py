# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json,datetime,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
H=json.loads((R/'hand-oracle.json').read_text())
def check(case,r):
 e=H['cases'][case];assert r['inputs']==dict(zip(['stride','last','pad','binding'],e['input']))
 assert r['input_hex']==''.join(H['word_hex_le'][str(v)] for v in e['words'])
 assert [w['offset'] for w in r['words']]==[0,4,8,12,16,20,24,28]
 assert [w['f32'] for w in r['words']]==e['words']
 assert [w['u32'] for w in r['words']]==[H['u32_bits'][str(v)] for v in e['words']]
 assert r['read_offsets']==H['wgsl_read_offsets']
 assert r['shader_sha256']==hashlib.sha256((R/'shader.wgsl').read_bytes()).hexdigest()
 assert r['resources_destroyed']==3 and r['device_destroyed'] and r['compilation_messages']==[]
 if case=='short-binding':
  assert r['status']=='VALIDATION_ERROR' and not r['gpu_submitted'] and not r['gpu_readback'] and r['readback'] is None and r['readback_bits'] is None
  assert r['validation_error']['name']=='GPUValidationError' and '28' in r['validation_error']['message'] and '32' in r['validation_error']['message']
 else:
  assert r['status']=='GPU_SUCCESS' and r['gpu_submitted'] and r['gpu_readback'] and r['validation_error'] is None
  assert r['readback']==e['readback'] and r['readback_bits']==[H['u32_bits'][str(v)] for v in e['readback']]
 assert r['adapter']['vendor']=='apple' and r['adapter']['architecture']=='metal-3' and 'Chrome/154' in r['runtime']
 assert datetime.datetime.fromisoformat(r['started_utc'].replace('Z','+00:00'))<=datetime.datetime.fromisoformat(r['ended_utc'].replace('Z','+00:00'))
