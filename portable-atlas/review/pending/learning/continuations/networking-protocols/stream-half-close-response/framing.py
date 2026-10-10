import sys
sys.dont_write_bytecode=True
import re
def validate(f,mode,width):
 if type(f) is not dict or set(f)!={'id','label','wire'} or type(f['id']) is not str or type(f['label']) is not str:raise ValueError('exact fixture')
 w=f['wire']
 if type(w) is not str or len(w)>36 or len(w)%2 or re.fullmatch('[0-9a-f]*',w) is None:raise ValueError('wire lower hex <=18bytes')
 if type(mode) is not str or mode not in ('normal','fault'):raise ValueError('mode')
 if type(width) is not int or width not in (1,64):raise ValueError('recv width')
def classify(chunks):
 data=b''.join(chunks)
 if len(data)<2:return dict(kind='header_eof',body_hex='')
 size=(data[0]<<8)|data[1]
 if size<1 or size>16:return dict(kind='invalid_length',body_hex='')
 if len(data)<2+size:return dict(kind='body_eof',body_hex='')
 if len(data)>2+size:return dict(kind='trailing',body_hex='')
 return dict(kind='complete',body_hex=data[2:].hex())
def reply(decision):
 body=b'ACK:'+bytes.fromhex(decision['body_hex']) if decision['kind']=='complete' else ('ERR:'+decision['kind']).encode('ascii')
 return len(body).to_bytes(2,'big')+body
