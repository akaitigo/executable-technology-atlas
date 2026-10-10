import sys
sys.dont_write_bytecode=True
# Independent literals fixed before producer; no framing or socket implementation imports.
HAND={
 'ping':('complete','000841434b3a50494e47'),
 'utf8':('complete','000641434b3acf80'),
 'maximum':('complete','001441434b3a4142434445464748494a4b4c4d4e4f50'),
 'header':('header_eof','000e4552523a6865616465725f656f66'),
 'body':('body_eof','000c4552523a626f64795f656f66'),
 'empty':('header_eof','000e4552523a6865616465725f656f66'),
 'zero':('invalid_length','00124552523a696e76616c69645f6c656e677468'),
 'over':('invalid_length','00124552523a696e76616c69645f6c656e677468'),
 'trailing':('trailing','000c4552523a747261696c696e67')}
def decode(wire):
 b=bytes.fromhex(wire)
 if len(b)<2:return 'header_eof'
 n=int.from_bytes(b[:2],'big')
 if n not in range(1,17):return 'invalid_length'
 return 'body_eof' if n>len(b[2:]) else 'trailing' if n<len(b[2:]) else 'complete'
def validate_observation(row,f):
 assert row['execution_status']=='passed' and row['closed_filenos']==[-1,-1]
 assert row['request_received_hex']==f['wire'] and row['request_decision']['kind']==HAND[f['id']][0]==decode(f['wire'])
 expected=HAND[f['id']][1] if row['mode']=='normal' else ''
 assert row['response_received_hex']==row['response_sent_hex']==expected
 assert row['protocol_outcome']==('missing_response' if row['mode']=='fault' else 'normal' if HAND[f['id']][0]=='complete' else 'refusal')
 trace=row['trace']
 for end,wire in [('B',f['wire']),('A',expected)]:
  received=[s for s in trace if s['endpoint']==end and s['api']=='recv' and s['result']=='data']
  assert ''.join(s['hex'] for s in received)==wire
  assert all(0<s['bytes']<=row['width'] and s['bytes']==len(bytes.fromhex(s['hex'])) for s in received)
  eof=[s for s in trace if s['endpoint']==end and s['api']=='recv' and s['result']=='eof'];assert len(eof)==1 and eof[0]['bytes']==0
  assert eof[0]['states'][end]['rx']=='eof' and eof[0]['states'][end]['tx']==('open' if end=='B' else 'shut_wr')
 if row['mode']=='normal':
  before=next(s for s in trace if s['endpoint']=='B' and s['api']=='sendall');assert before['states']['B']==dict(tx='open',rx='eof')
  assert trace.index(before)>next(i for i,s in enumerate(trace) if s['endpoint']=='B' and s['api']=='recv' and s['result']=='eof')
 assert trace[-1]['states']=={'A':{'tx':'closed','rx':'closed'},'B':{'tx':'closed','rx':'closed'}}
