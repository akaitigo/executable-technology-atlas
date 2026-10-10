"""Atlas: independent saved-file inspection; no producer import or execution."""
from copy import deepcopy
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
RUN = BASE/'observations/run-01'

def sha(data):return 'sha256:'+hashlib.sha256(data).hexdigest()

def inspect(raw, cases, expected, artifacts):
    count = 0
    def eq(actual,wanted,name):
        nonlocal count
        count += 1
        if actual!=wanted:raise AssertionError(name+': '+repr(actual)+' != '+repr(wanted))
    baseline=artifacts['artifacts/baseline.tar'];changed=artifacts['artifacts/changed.tar']
    for blob,body in [(baseline,b'Atlas\n'),(changed,b'atlas\n')]:
        eq(len(blob),2048,'tar length');h=blob[:512]
        eq(h[:100].split(b'\0')[0],b'lesson.txt','name')
        for a,z,n in [(100,108,420),(108,116,0),(116,124,0),(124,136,6),(136,148,0)]:eq(int(h[a:z].rstrip(b'\0 '),8),n,'tar numeric field')
        eq(h[156:157],b'0','file type');eq(h[257:263],b'ustar\0','magic');eq(h[263:265],b'00','version')
        eq(int(h[148:156].rstrip(b'\0 '),8),sum(h[:148])+8*32+sum(h[156:]),'checksum')
        eq(blob[512:518],body,'member content');eq(blob[518:],bytes(1530),'padding and end blocks')
    eq(baseline[:512],changed[:512],'same metadata')
    eq(raw['tar']['diffId'],sha(baseline),'baseline DiffID');eq(raw['tar']['changedDiffId'],sha(changed),'changed DiffID')
    eq(raw['relationships'],expected['relationships'],'fixed relations')
    for name,asset in raw['assets'].items():
        blob=artifacts[asset['file']]
        eq(asset['bytes'],len(blob),'asset size');eq(asset['digest'],sha(blob),'asset digest')
        eq(asset['headerHex'],blob[:10].hex(),'gzip header')
        eq(asset['mtime'],int.from_bytes(blob[4:8],'little'),'mtime')
    a=artifacts['artifacts/mtime0.gz'];b=artifacts['artifacts/mtime1.gz']
    eq(len(a),len(b),'same compressed size');eq(a==b,False,'different compressed bytes')
    eq([i for i,(x,y)in enumerate(zip(a,b))if x!=y],[4],'only mtime byte differs')
    eq(a[:4],bytes.fromhex('1f8b0800'),'gzip fixed header')
    eq(int.from_bytes(a[4:8],'little'),0,'mtime0');eq(int.from_bytes(b[4:8],'little'),1,'mtime1')
    for blob in [a,b]:
        with gzip.GzipFile(fileobj=io.BytesIO(blob),mode='rb') as reader:
            decoded=reader.read(4097)
        eq(decoded,baseline,'separate bounded gzip read')
    eq(artifacts['artifacts/header-tamper.gz'],b,'header tamper same as mtime1')
    eq(artifacts['artifacts/truncated.gz'],a[:-4],'truncation')
    crc=bytearray(a);crc[-8]^=1;eq(artifacts['artifacts/bad-crc.gz'],bytes(crc),'CRC change')
    eq(artifacts['artifacts/trailing.gz'],a+b'X','trailing byte')
    eq(artifacts['artifacts/concatenated.gz'],a+a,'concatenation')
    eq([r['id'] for r in raw['cases']],[r['id'] for r in cases['cases']],'case set/order')
    by_id={r['id']:r for r in expected['rows']}
    for result,case in zip(raw['cases'],cases['cases']):
        hand=by_id[case['id']];out=result['outcome'];d=out['diagnostics'];blob=artifacts[result['input']['blobFile']]
        for name in ['id','label','variant','mode','outputCap']:eq(result[name],case[name],'case input')
        eq(result['input']['outputCap'],case['outputCap'],'consumer cap')
        eq(result['input']['expectedDiffId'],sha(baseline),'fixed trusted DiffID')
        desc={'mediaType':'application/vnd.oci.image.layer.v1.tar+gzip','size':len(blob),'digest':sha(blob)}
        if case['id']=='header-tamper':desc['digest']=sha(a)
        if case['id']=='wrong-size':desc['size']+=1
        eq(result['input']['descriptor'],desc,'descriptor fixture');eq(result['descriptorAfter'],desc,'descriptor unchanged')
        eq(out['accepted'],hand['accepted'],'accepted');eq(out['reason'],hand['reason'],'reason')
        eq(out['payload'] is not None,hand['successfulPayloadPresent'],'payload presence')
        eq(out['trace'][-1],{'stage':hand['reason'],'accepted':hand['accepted']},'final stage')
        eq(d['compressedBytes'],len(blob),'compressed byte count')
        eq(d['stagedBytes']<=case['outputCap']+1,True,'bounded diagnostic')
        eq(0<=d['inflateCalls']<=128,True,'bounded calls')
        early=case['id']in ['wrong-size','header-tamper','conflated-check']
        eq(d['gzipStarted'],not early,'gzip stage reached')
        eq(d['compressedDigest'],None if case['id']=='wrong-size'else sha(blob),'digest stage reached')
        if hand['accepted']:
            eq(out['payload'],{'tarBytes':2048,'diffId':sha(baseline)},'success payload')
            eq(bytes.fromhex(d['acceptedTarHex']),baseline,'success bytes')
            eq(d['gzipEof'],True,'complete member');eq(d['trailingBytes'],0,'no trailing')
        else:
            eq(out['payload'],None,'no successful payload')
            eq('acceptedTarHex'in d,False,'no accepted bytes on refusal')
        if case['id']=='changed-content':eq(d['observedDiffId'],sha(changed),'changed content DiffID')
        if case['id']=='output-limit':eq(d['stagedBytes'],2048,'cap+1 sentinel')
        if case['id']in ['trailing','concatenated']:eq(d['trailingBytes'],1 if case['id']=='trailing'else len(a),'remaining data')
    return count

def main():
    raw=json.loads((RUN/'results.json').read_text());cases=json.loads((BASE/'cases.json').read_text());expected=json.loads((BASE/'expected.json').read_text())
    artifacts={str(p.relative_to(RUN)):p.read_bytes()for p in (RUN/'artifacts').iterdir()if p.is_file()}
    checks=inspect(raw,cases,expected,artifacts)
    bindings={}
    for name,digest in raw['inputs'].items():
        if hashlib.sha256((BASE/name).read_bytes()).hexdigest()!=digest or hashlib.sha256((RUN/'inputs'/name).read_bytes()).hexdigest()!=digest:raise AssertionError('input changed: '+name)
        bindings[name]=digest
    mutations=[]
    for label in ['missing-case','conflated-identities','false-accept','denied-payload','cap-hidden','blob-altered']:
        altered=deepcopy(raw);files=dict(artifacts)
        if label=='missing-case':altered['cases'].pop()
        elif label=='conflated-identities':altered['relationships']['compressedDigestsEqual']=True
        elif label=='false-accept':altered['cases'][4]['outcome']['accepted']=True
        elif label=='denied-payload':altered['cases'][5]['outcome']['payload']={}
        elif label=='cap-hidden':altered['cases'][5]['outcome']['diagnostics']['stagedBytes']=2047
        else:files['artifacts/mtime0.gz']=files['artifacts/mtime0.gz'][:-1]+b'X'
        try:inspect(altered,cases,expected,files)
        except (AssertionError,KeyError,IndexError):mutations.append(label)
        else:raise AssertionError('mutation survived: '+label)
    report={'Atlas':'保存OCI計算の照合','at':datetime.now(timezone.utc).isoformat(),'passed':True,'checks':checks,'memoryMutationsRejected':mutations,'inputBindings':bindings,'producerImported':False,'producerExecuted':False,'hostExtraction':False,'guiChecked':False}
    if '--record'in sys.argv:
        with (BASE/'verification/saved-result-check.json').open('x')as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
