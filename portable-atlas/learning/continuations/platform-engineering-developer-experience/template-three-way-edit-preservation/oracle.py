# SPDX-License-Identifier: Apache-2.0
import json,hashlib
# Independent literal bytes; no merge function, runner or branch predicates.
USER_B='{"description":"user","owner":"team-b","templateVersion":1}\n'
EXPECTED={
 'preserve':('APPLIED',1,[],'{"description":"user","owner":"team-b","templateVersion":2}\n'),
 'template-only':('APPLIED',1,[],'{"description":"new","owner":"team-a","templateVersion":2}\n'),
 'conflict':('CONFLICT',0,['description'],'{"description":"user","owner":"team-a","templateVersion":1}\n'),
 'same-change':('APPLIED',1,[],'{"description":"new","owner":"team-a","templateVersion":2}\n'),
 'overwrite-fault':('APPLIED',1,[],'{"description":"base","owner":"team-a","templateVersion":2}\n'),
 'owner-conflict':('CONFLICT',0,['owner'],'{"description":"base","owner":"team-b","templateVersion":1}\n'),
 'version-conflict':('CONFLICT',0,['templateVersion'],'{"description":"base","owner":"team-a","templateVersion":2}\n'),
 'refusal':('REFUSED_INPUT',0,[],None),
 'failure':('EXECUTION_FAILURE',0,[],USER_B)}
def check(r,files=None):
 assert r['python']=='3.9.6' and r['started_utc']<=r['ended_utc']
 status,writes,fields,b=EXPECTED[r['case']]
 assert (r['status'],r['apply_writes'],r['conflicts'],r['after_bytes'])==(status,writes,fields,b)
 if b is None:assert r['setup_writes']==0 and not r['fixture_created'] and r['before_bytes'] is None;return
 assert r['setup_writes']==1 and r['fixture_created'] and r['tmp_cleanup'] and r['final']==json.loads(b)
 assert r['after_sha256']==hashlib.sha256(b.encode()).hexdigest() and r['before_sha256']==hashlib.sha256(r['before_bytes'].encode()).hexdigest()
 if status=='CONFLICT':assert r['before_bytes']==b and r['apply_attempts']==0
 if status=='EXECUTION_FAILURE':assert r['before_bytes']==USER_B and r['error_class']=='NotADirectoryError' and r['errno']==20 and '<owned-tmp>' in r['error_message']
 if files:
  assert (files/'after.json').read_bytes()==b.encode() and (files/'before.json').read_bytes()==r['before_bytes'].encode()
