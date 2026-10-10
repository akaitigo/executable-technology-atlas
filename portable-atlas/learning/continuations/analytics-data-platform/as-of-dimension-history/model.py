# SPDX-License-Identifier: Apache-2.0
import sqlite3
ASOF="SELECT o.id,o.customer,o.t,o.amount,d.version,d.region FROM orders o LEFT JOIN dimension d ON o.customer=d.customer AND d.valid_from<=o.t AND o.t<d.valid_to ORDER BY o.id,d.version"
LATEST="SELECT o.id,o.customer,o.t,o.amount,d.version,d.region FROM orders o LEFT JOIN dimension d ON o.customer=d.customer AND d.valid_from=(SELECT MAX(x.valid_from) FROM dimension x WHERE x.customer=o.customer) ORDER BY o.id,d.version"
BROKEN="SELECT absent_column FROM orders"
def validate(c):
 if c.get('method') not in ('asof','latest','broken'):raise ValueError('method')
 ids=set();versions=set()
 for v,k,region,start,end in c['versions']:
  if type(v) is not int or not 1<=v<=32 or v in versions:raise ValueError('version')
  versions.add(v)
  if k!='c1' or region not in ('north','south'):raise ValueError('dimension text')
  if type(start) is not int or type(end) is not int or not 0<=start<end<=20:raise ValueError('interval')
 if not c['versions']:raise ValueError('empty history')
 for oid,key,t,amount in c['orders']:
  if not isinstance(oid,str) or not oid or oid in ids:raise ValueError('order id')
  ids.add(oid)
  if key not in ('c1','c9'):raise ValueError('customer')
  if type(t) is not int or not 0<=t<=20:raise ValueError('time')
  if type(amount) is not int or not 0<=amount<=1000:raise ValueError('amount')
 if not ids:raise ValueError('empty orders')
def run(c):
 try:validate(c)
 except (ValueError,KeyError,TypeError) as e:return dict(status='REFUSED_INVALID_INPUT',reason=str(e),sql=None,rows=[],orders=[],aggregate=None)
 sql={'asof':ASOF,'latest':LATEST,'broken':BROKEN}[c['method']]
 with sqlite3.connect(':memory:') as db:
  db.executescript('CREATE TABLE dimension(version INTEGER PRIMARY KEY,customer TEXT,region TEXT,valid_from INTEGER,valid_to INTEGER); CREATE TABLE orders(id TEXT PRIMARY KEY,customer TEXT,t INTEGER,amount INTEGER);')
  db.executemany('INSERT INTO dimension VALUES(?,?,?,?,?)',c['versions']);db.executemany('INSERT INTO orders VALUES(?,?,?,?)',c['orders'])
  try:rows=[list(x) for x in db.execute(sql)]
  except sqlite3.Error as e:return dict(status='EXECUTION_FAILURE',reason=type(e).__name__+': '+str(e),sql=sql,rows=[],orders=[],aggregate=None)
  out=[];agg={};multiple=False
  known={v[1] for v in c['versions']}
  for oid,key,t,amount in c['orders']:
   matches=[x for x in rows if x[0]==oid and x[4] is not None]
   kind='MULTIPLE_MATCH' if len(matches)>1 else 'MATCHED' if matches else 'GAP' if key in known else 'UNKNOWN_KEY'
   multiple|=len(matches)>1
   out.append(dict(id=oid,time=t,amount=amount,classification=kind,versions=[x[4] for x in matches],regions=[x[5] for x in matches]))
   bucket=matches[0][5] if len(matches)==1 else kind
   agg[bucket]=agg.get(bucket,0)+amount
  return dict(status='REFUSED_MULTIPLE_MATCH' if multiple else 'OK',reason='multiple versions for an order' if multiple else '',sql=sql,rows=rows,orders=out,aggregate=None if multiple else agg)
