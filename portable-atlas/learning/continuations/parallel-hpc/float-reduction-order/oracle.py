# SPDX-License-Identifier: Apache-2.0
from fractions import Fraction
EXPECTED={'left':([0,1,2,3],[1e16,1e16,0,1],1,'-1'),'tree':([0,1,2,3],[[1e16,-1e16],[0]],0,'-2'),'fsum':([0,1,2,3],[2],2,'0'),'drop-small':([0,2,3],[1e16,0,1],1,'-1'),'drop-cancel':([1,3],[1,2],2,'0')}
def check(r):
 assert r['python']=='3.9.6' and (r['radix'],r['mantissa'],r['rounds'])==(2,53,1)
 assert r['started_utc']<=r['ended_utc'] and r['started_utc'].endswith('+00:00')
 n=r['case']
 if n=='refusal':assert r['status']=='REFUSED_INPUT' and r['stage']=='validation' and r['result'] is None and not r['steps'];return
 if n=='failure':assert r['status']=='EXECUTION_FAILURE' and r['stage']=='executor' and r['error_class']=='RuntimeError' and r['error_message']=='injected executor failure' and r['result'] is None;return
 target=Fraction(0)
 for x in r['inputs']:target+=Fraction(*float(x).as_integer_ratio())
 assert target==2
 ids,steps,result,error=EXPECTED[n]
 assert r['ids']==ids and r['count']==len(ids) and r['steps']==steps and r['result']==result
 assert str(Fraction(*float(r['result']).as_integer_ratio())-target)==error
 assert r['status']==('OK' if ids==[0,1,2,3] else 'INCLUSION_VIOLATION') and r['stage']=='complete'
