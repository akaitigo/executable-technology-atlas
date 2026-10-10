import sys
sys.dont_write_bytecode=True
import hashlib,hmac
# Published synthetic key, not a credential.
PUBLIC_FIXTURE_KEY=b'atomic-admission-public-fixture-key-v1'
def request(identifier,payload='',valid=True):
 tag=hmac.new(PUBLIC_FIXTURE_KEY,identifier.encode('ascii')+b'\0'+payload.encode('utf-8'),hashlib.sha256).hexdigest() if valid else '0'*64
 return dict(id=identifier,payload=payload,tag=tag)
def fixture(id,label,a,b,seen=None):return dict(id=id,label=label,requests=[a,b],seen=[] if seen is None else seen)
FIXTURES=[
 fixture('same','同じID・両方認証成功',request('MSG1'),request('MSG1')),
 fixture('different','異なるID',request('MSG1','a'),request('MSG2','b')),
 fixture('preseen','事前登録済ID',request('MSG1'),request('MSG1'),['MSG1']),
 fixture('invalid','両方invalid MAC',request('MSG1',valid=False),request('MSG1',valid=False),['KEEP']),
 fixture('mixed','A invalid / B valid',request('MSG1',valid=False),request('MSG1')),
 fixture('payload','同じID・異なるpayload',request('MSG1','left'),request('MSG1','right')),
 fixture('boundary','ID16文字・payload64bytes',request('ABCDEFGHIJKLMNOP','π'*32),request('ABCDEFGHIJKLMNOP','π'*32))]
