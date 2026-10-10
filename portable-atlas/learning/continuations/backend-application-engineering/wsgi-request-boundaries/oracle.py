"""Independent literal HTTP table plus direct read-only SQL; no producer imports."""
import json,sqlite3,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TABLE=json.loads((ROOT/'oracle.json').read_text())
def validate(raw):
 assert raw['exit_code']==0 and raw['execution_failures']==0
 flat=[c for g in raw['groups'] for c in g['cases']];assert [c['id'] for c in flat]==list(TABLE['cases'])
 for group,fixture_group in zip(raw['groups'],raw['fixture']['groups']):
  assert group['id']==fixture_group['id'] and group['host']=='127.0.0.1' and group['port']>0 and all(group['cleanup'].values())
  assert [c['request'] for c in group['cases']]==fixture_group['cases']
 for c in flat:
  expected=TABLE['cases'][c['id']];response=c['response'];a=c['app'];assert response['status']==a['status']==expected['status'];assert response['body']==a['response_body']==expected['body'];assert json.loads(bytes.fromhex(response['body_hex']))==expected['body'];headers=dict(response['headers']);assert headers['Content-Type']=='application/json' and int(headers['Content-Length'])==len(bytes.fromhex(response['body_hex']))
  assert a['acquired']==expected['acquired'] and a['closed']==expected['closed'];assert c['http_client_closed'];assert a['server_streams_closed_by_app'] is False and a['input_closed_at_response'] is False and a['errors_closed_at_response'] is False
  env=a['environ'];req=c['request'];assert env['REQUEST_METHOD']==req['method'] and env['PATH_INFO']==req['path'];assert not env['wsgi.multithread'] and not env['wsgi.multiprocess']
  events=[e['event'] for e in a['events']];assert [e['seq'] for e in a['events']]==list(range(len(events)))
  if expected['status']==201:
   assert events==TABLE['event_success'];assert 'COMMIT' in a['sql_trace'] and 'ROLLBACK' not in a['sql_trace'];assert c['error_stream_delta']==''
  elif expected['status']==500:
   assert events==TABLE['event_fault'];assert a['exception']==dict(type='OperationalError',message='no such table: missing_outbox');assert 'ROLLBACK' in a['sql_trace'] and 'COMMIT' not in a['sql_trace'];assert c['error_stream_delta']=='lesson storage failure: OperationalError\n'
  else:
   assert events==(['request_received','input_read','response_start'] if c['id'] in ['invalid-json','bool-units'] else ['request_received','response_start']);assert not a['sql_trace'] and 'connection_token' not in a
  if expected['acquired']:
   assert a['closed_probe']['type']=='ProgrammingError';assert events.index('connection_closed')<events.index('response_start')
  if 'input_read' in events:
   assert bytes.fromhex(a['request_body_hex'])==req['body'].encode();e=a['events'][1];assert e['actual']==e['requested']==int(req['headers']['Content-Length'])<=128
  db=ROOT/c['db_snapshot'];assert hashlib.sha256(db.read_bytes()).hexdigest()==c['db_sha256'];connection=sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True)
  try:
   orders=[list(r) for r in connection.execute(TABLE['queries'][0])];outbox=[list(r) for r in connection.execute(TABLE['queries'][1])];integrity=connection.execute('PRAGMA integrity_check').fetchone()[0]
  finally:connection.close()
  assert orders==expected['orders'] and outbox==expected['outbox'] and integrity=='ok';assert c['independent_observer']==dict(orders=orders,outbox=outbox,integrity=integrity)
 recovery=raw['groups'][2]['cases'];assert recovery[0]['app']['connection_token']=='request-connection-1';assert recovery[1]['app']['connection_token']=='request-connection-2'
 return dict(cases=11,normal_http=2,input_refusals=8,expected_sql_faults=1,execution_failures=0,request_acquisitions=3,request_closes=3,recovery_new_connection=True)
