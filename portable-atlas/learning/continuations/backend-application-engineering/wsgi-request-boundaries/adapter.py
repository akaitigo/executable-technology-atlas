"""Finite actual WSGI JSON adapter. Status mapping and fault header are lesson-specific."""
import json,sqlite3,re,datetime
class App:
 def __init__(self,path):self.path=path;self.requests=[];self.next_connection=0
 def __call__(self,environ,start_response):
  row=dict(events=[],sql_trace=[],acquired=0,closed=0,environ={k:environ.get(k) for k in ['REQUEST_METHOD','PATH_INFO','CONTENT_LENGTH','CONTENT_TYPE','HTTP_TRANSFER_ENCODING','wsgi.multithread','wsgi.multiprocess']});self.requests.append(row)
  def event(name,**fields):row['events'].append(dict(event=name,seq=len(row['events']),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**fields))
  event('request_received');status=400;body=None
  if environ['PATH_INFO']!='/orders':status,body=404,dict(error='route not found')
  elif environ['REQUEST_METHOD']!='POST':status,body=405,dict(error='method must be POST')
  elif environ.get('HTTP_TRANSFER_ENCODING'):status,body=400,dict(error='Transfer-Encoding unsupported')
  elif environ.get('CONTENT_TYPE')!='application/json':status,body=415,dict(error='Content-Type must be application/json')
  else:
   length=environ.get('CONTENT_LENGTH','')
   if not length:status,body=411,dict(error='Content-Length required')
   elif not re.fullmatch('[0-9]+',length):body=dict(error='invalid Content-Length')
   elif int(length)>128:status,body=413,dict(error='body exceeds 128 bytes')
   elif int(length)<1:body=dict(error='body must be nonempty')
   else:
    data=environ['wsgi.input'].read(int(length));row['request_body_hex']=data.hex();event('input_read',requested=int(length),actual=len(data))
    try:req=json.loads(data.decode('utf-8'))
    except (ValueError,UnicodeError):body=dict(error='invalid JSON')
    else:
     if not isinstance(req,dict) or set(req)!={'units'} or type(req.get('units')) is not int or not 1<=req['units']<=3:body=dict(error='units must be integer 1..3')
     else:
      event('input_validated');connection=None
      try:
       connection=sqlite3.connect(self.path,isolation_level=None);connection.set_trace_callback(row['sql_trace'].append);self.next_connection+=1;row['connection_token']='request-connection-'+str(self.next_connection);row['acquired']=1;event('connection_acquired',token=row['connection_token'])
       connection.execute('BEGIN IMMEDIATE');event('transaction_begin');cursor=connection.execute('INSERT INTO orders(units) VALUES (?)',(req['units'],));order_id=cursor.lastrowid;event('orders_inserted',order_id=order_id)
       if environ.get('HTTP_X_LESSON_FAULT')=='second-sql':
        event('fault_before_second_sql',sql='INSERT INTO missing_outbox(order_id,event) VALUES (?,?)');connection.execute('INSERT INTO missing_outbox(order_id,event) VALUES (?,?)',(order_id,'order.created'))
       else:connection.execute('INSERT INTO outbox(order_id,event) VALUES (?,?)',(order_id,'order.created'));event('outbox_inserted')
       connection.execute('COMMIT');event('transaction_commit');status,body=201,dict(order_id=order_id,amount=100*req['units'])
      except sqlite3.Error as e:
       row['exception']=dict(type=type(e).__name__,message=str(e));event('sql_exception',**row['exception']);environ['wsgi.errors'].write('lesson storage failure: '+type(e).__name__+'\n');environ['wsgi.errors'].flush()
       if connection is not None and connection.in_transaction:connection.execute('ROLLBACK');event('transaction_rollback')
       status,body=500,dict(error='storage failure')
      finally:
       if connection is not None:
        connection.close();row['closed']+=1;event('connection_closed',token=row['connection_token'])
        try:connection.execute('SELECT 1')
        except sqlite3.ProgrammingError as e:row['closed_probe']=dict(type=type(e).__name__,message=str(e));event('closed_probe_refused',**row['closed_probe'])
  if body is None:raise AssertionError('response missing')
  row['server_streams_closed_by_app']=False;row['input_closed_at_response']=getattr(environ['wsgi.input'],'closed',None);row['errors_closed_at_response']=getattr(environ['wsgi.errors'],'closed',None)
  encoded=json.dumps(body,separators=(',',':')).encode('utf-8');reasons={201:'Created',400:'Bad Request',404:'Not Found',405:'Method Not Allowed',411:'Length Required',413:'Payload Too Large',415:'Unsupported Media Type',500:'Internal Server Error'};event('response_start',status=status);row.update(status=status,response_body=body)
  start_response(str(status)+' '+reasons[status],[('Content-Type','application/json'),('Content-Length',str(len(encoded)))]);return [encoded]
