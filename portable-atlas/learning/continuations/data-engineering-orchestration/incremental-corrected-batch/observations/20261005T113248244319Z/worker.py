#!/usr/bin/env python3
import argparse,hashlib,json,sqlite3,sys
class Refusal(Exception):pass
def payload(e):return hashlib.sha256(json.dumps(e,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def main():
 a=argparse.ArgumentParser();a.add_argument('--db',required=True);a.add_argument('--input',required=True);a.add_argument('--strategy',choices=['replace','append','keyed'],required=True);args=a.parse_args()
 events=json.load(open(args.input));c=sqlite3.connect(args.db,isolation_level=None,timeout=.1);trace=[];actions=[]
 def sql(q,params=()):
  rows=[list(x) for x in c.execute(q,params)];trace.append({'sql':q,'params':list(params),'rows':rows});return rows
 before=sql('SELECT key,price FROM items ORDER BY key,price');code=0;reason=None
 try:
  ids=[e['eventId'] for e in events]
  for i,v in enumerate(ids):
   if v in ids[:i]:raise Refusal('duplicate-event-id:'+v)
  sql('BEGIN IMMEDIATE')
  if args.strategy=='replace':sql('DELETE FROM items')
  for e in events:
   if args.strategy!='keyed':
    if e['op']=='upsert':sql('INSERT INTO items(key,price) VALUES(?,?)',(e['key'],e['price']));actions.append({'eventId':e['eventId'],'action':'insert'})
    else:actions.append({'eventId':e['eventId'],'action':'delete-ignored-by-snapshot-strategy'})
    continue
   prior=sql('SELECT payload_sha FROM applied WHERE event_id=?',(e['eventId'],))
   if prior:
    if prior[0][0]!=payload(e):raise Refusal('event-id-payload-conflict:'+e['eventId'])
    actions.append({'eventId':e['eventId'],'action':'already-applied'});continue
   if e['op']=='upsert':sql('INSERT INTO items(key,price) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET price=excluded.price',(e['key'],e['price']))
   elif e['op']=='delete':
    if not sql('SELECT key FROM items WHERE key=?',(e['key'],)):raise Refusal('unknown-delete:'+e['key'])
    sql('DELETE FROM items WHERE key=?',(e['key'],))
   else:raise Refusal('unknown-op:'+e['op'])
   sql('INSERT INTO applied(event_id,payload_sha) VALUES(?,?)',(e['eventId'],payload(e)));actions.append({'eventId':e['eventId'],'action':e['op']})
  sql('COMMIT')
 except Refusal as e:
  code=2;reason=str(e)
  if c.in_transaction:sql('ROLLBACK')
 except Exception as e:
  code=1;reason=type(e).__name__+': '+str(e)
  if c.in_transaction:sql('ROLLBACK')
 after=sql('SELECT key,price FROM items ORDER BY key,price');ledger=sql('SELECT event_id,payload_sha FROM applied ORDER BY event_id');c.close()
 print(json.dumps({'strategy':args.strategy,'before':before,'events':events,'order':[e['eventId'] for e in events],'after':after,'count':len(after),'sum':sum(x[1] for x in after),'ledger':ledger,'actions':actions,'reason':reason,'exitCode':code,'sqlTrace':trace}));return code
if __name__=='__main__':sys.exit(main())
