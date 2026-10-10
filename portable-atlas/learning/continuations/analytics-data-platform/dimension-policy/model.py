"""Atlas: actual SQLite quality-policy comparisons in owned memory connections."""
import sqlite3

POLICIES=['reject-batch','quarantine-row','retain']
METRIC='accepted orders with at least one line; sum known amounts; report missing denominator'
class Refusal(ValueError):pass
def validate(x):
 if type(x) is not dict or set(x)!={'schema','customers','orders','lines','policies','null_customer_policy','metric'}:raise Refusal('input_keys')
 if type(x['schema']) is not int or x['schema']!=1:raise Refusal('schema')
 if x['policies']!=POLICIES:raise Refusal('policies')
 if x['null_customer_policy']!='allow':raise Refusal('null_policy')
 if x['metric']!=METRIC:raise Refusal('metric')
 for key,n,width in [('customers',2,2),('orders',6,3),('lines',6,2)]:
  rows=x[key]
  if type(rows) is not list or len(rows)!=n:raise Refusal(key+'_count')
  if any(type(r) is not list or len(r)!=width for r in rows):raise Refusal(key+'_shape')
  if any(type(r[0]) is not int or not 0<r[0]<=10000 for r in rows):raise Refusal(key+'_id')
  if len({r[0] for r in rows})!=n:raise Refusal(key+'_duplicate')
 if any(type(r[1]) is not str or not 0<len(r[1])<=32 for r in x['customers']):raise Refusal('region')
 if any(r[1] is not None and (type(r[1]) is not int or not 0<r[1]<=10000) for r in x['orders']):raise Refusal('customer_key')
 if any(r[2] is not None and (type(r[2]) is not int or not 0<=r[2]<=10000) for r in x['orders']):raise Refusal('amount')
 if any(type(r[1]) is not int or r[1] not in {o[0] for o in x['orders']} for r in x['lines']):raise Refusal('line_order')
 return x
def rows(db,sql):return [list(r) for r in db.execute(sql).fetchall()]
def ids(db,sql):return [r[0] for r in db.execute(sql).fetchall()]
def opened(cleanup):
 db=sqlite3.connect(':memory:',isolation_level=None);cleanup['opened']+=1;return db
def close(db,cleanup):
 db.close();cleanup['closed']+=1
def policy_case(x,q,policy,cleanup):
 validate(x)
 if policy not in POLICIES:raise Refusal('unknown_policy')
 db=opened(cleanup)
 try:
  db.execute('PRAGMA foreign_keys=ON');fk=db.execute('PRAGMA foreign_keys').fetchone();assert fk==(1,),'foreign-key support required'
  db.executescript(q['schema']);db.executemany('INSERT INTO customers VALUES (?,?)',x['customers']);db.executemany('INSERT INTO stage_orders VALUES (?,?,?)',x['orders']);db.executemany('INSERT INTO lines VALUES (?,?)',x['lines'])
  classification=rows(db,q['classification']);unknown=ids(db,"SELECT order_id FROM classified WHERE key_state='unknown' ORDER BY order_id")
  db.execute('INSERT INTO accepted SELECT order_id FROM classified WHERE '+q['accept_predicates'][policy])
  if policy=='reject-batch' and unknown:db.execute("INSERT INTO rejected SELECT order_id,'batch_rejected_unknown_key' FROM classified")
  if policy=='quarantine-row':db.execute("INSERT INTO quarantined SELECT order_id,'unknown_customer_key' FROM classified WHERE key_state='unknown'")
  accepted=ids(db,'SELECT order_id FROM accepted ORDER BY order_id');quarantine=rows(db,'SELECT * FROM quarantined ORDER BY order_id');rejected=rows(db,'SELECT * FROM rejected ORDER BY order_id')
  metric_ids=ids(db,q['metric_ids']);amount,n,known,missing=db.execute(q['metric']).fetchone();candidate=ids(db,'SELECT order_id FROM classified WHERE line_count>0 ORDER BY order_id')
  decisions=rows(db,"SELECT c.order_id,CASE WHEN a.order_id IS NOT NULL THEN 'accepted' WHEN z.order_id IS NOT NULL THEN 'quarantined' WHEN r.order_id IS NOT NULL THEN 'rejected' ELSE 'unassigned' END,CASE WHEN a.order_id IS NOT NULL AND c.line_count>0 THEN 1 ELSE 0 END FROM classified c LEFT JOIN accepted a ON a.order_id=c.order_id LEFT JOIN quarantined z ON z.order_id=c.order_id LEFT JOIN rejected r ON r.order_id=c.order_id ORDER BY c.order_id")
  return {'policy':policy,'batch_status':'rejected' if rejected else 'accepted_with_quarantine' if quarantine else 'accepted','accepted_ids':accepted,'quarantined_ids':[r[0] for r in quarantine],'rejected_ids':[r[0] for r in rejected],'metric_ids':metric_ids,'accepted_but_no_line_ids':ids(db,'SELECT c.order_id FROM classified c JOIN accepted a ON a.order_id=c.order_id WHERE c.line_count=0 ORDER BY c.order_id'),'sum_amount':amount,'input_rows':n,'known_rows':known,'missing_rows':missing,'missing_fraction':{'numerator':missing,'denominator':n} if n else None,'candidate_coverage':{'numerator':n,'denominator':len(candidate)},'candidate_ids':candidate,'classification_rows':classification,'unknown_ids':unknown,'null_key_ids':ids(db,"SELECT order_id FROM classified WHERE key_state='null_key' ORDER BY order_id"),'decisions':decisions,'quarantine_records':quarantine,'rejection_records':rejected,'foreign_keys_readback':fk[0],'database':':memory:','source_id':db.execute('SELECT sqlite_source_id()').fetchone()[0],'publish_performed':False}
 finally:close(db,cleanup)
def fk_probe(x,q,enabled,cleanup):
 validate(x)
 if type(enabled) is not int or enabled not in [0,1]:raise Refusal('foreign_keys_setting')
 db=opened(cleanup)
 try:
  before=db.in_transaction;db.execute('PRAGMA foreign_keys='+str(enabled));actual=db.execute('PRAGMA foreign_keys').fetchone();assert actual==(enabled,),'foreign-key setting mismatch'
  db.executescript(q['fk_schema']);db.executemany('INSERT INTO customers VALUES (?,?)',x['customers']);events=[]
  for order in x['orders']:
   event={'order_id':order[0],'customer_id':order[1],'outcome':'inserted','error':None,'in_transaction_before':db.in_transaction}
   try:db.execute('INSERT INTO fk_orders VALUES (?,?,?)',order)
   except sqlite3.IntegrityError as e:
    if 'FOREIGN KEY constraint failed' not in str(e):raise
    event.update(outcome='foreign_key_constraint',error={'type':type(e).__name__,'message':str(e)})
   event.update(saved_ids=ids(db,'SELECT order_id FROM fk_orders ORDER BY order_id'),in_transaction_after=db.in_transaction);events.append(event)
  return {'foreign_keys':actual[0],'pragma_in_transaction':before,'outcomes':[e['outcome'] for e in events],'ids_after_each':[e['saved_ids'] for e in events],'saved_ids':ids(db,'SELECT order_id FROM fk_orders ORDER BY order_id'),'violations':rows(db,'PRAGMA foreign_key_check'),'quarantine_rows_created':0,'events':events,'schema_sql':q['fk_schema'],'rowid_order_id_pairs':rows(db,'SELECT rowid,order_id FROM fk_orders ORDER BY order_id'),'database':':memory:','isolation_level':db.isolation_level,'source_id':db.execute('SELECT sqlite_source_id()').fetchone()[0]}
 finally:close(db,cleanup)
