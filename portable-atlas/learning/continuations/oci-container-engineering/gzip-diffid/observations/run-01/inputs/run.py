"""Atlas: generate only owned memory/lesson bytes, then finite validation."""
from copy import deepcopy
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import tarfile
import time
import zlib
from layer import MEDIA, digest, verify_layer

BASE = Path(__file__).resolve().parent
INPUTS = ('CONTRACT.md','fixture.json','cases.json','expected.json','layer.py','run.py','verify.py')

def tar_bytes(info, body):
    entry = tarfile.TarInfo(info['name'])
    entry.size = len(body)
    for key in ('mode','uid','gid','mtime','uname','gname'):
        setattr(entry, key, info[key])
    entry.type = tarfile.REGTYPE
    entry.devmajor = entry.devminor = 0
    header = entry.tobuf(format=tarfile.USTAR_FORMAT)
    return header + body + bytes((-len(body)) % 512) + bytes(1024)

def gzip_bytes(data, mtime):
    output = io.BytesIO()
    with gzip.GzipFile(filename='', mode='wb', fileobj=output, compresslevel=6, mtime=mtime) as writer:
        writer.write(data)
    return output.getvalue()

def main():
    if os.getpriority(os.PRIO_PROCESS, 0) < 10:
        raise SystemExit('Atlas: actual nice10 required')
    directory = BASE/'observations/run-01'
    directory.mkdir(parents=True, exist_ok=False)
    (directory/'inputs').mkdir()
    (directory/'artifacts').mkdir()
    start = time.monotonic()
    result = {'Atlas':'OCI gzipとDiffIDの有限実計算','startedAt':datetime.now(timezone.utc).isoformat(),
              'python':platform.python_version(),'platform':platform.platform(),'zlibBuild':zlib.ZLIB_VERSION,
              'zlibRuntime':zlib.ZLIB_RUNTIME_VERSION,'actualNice':os.getpriority(os.PRIO_PROCESS,0),
              'inputs':{},'assets':{},'cases':[]}
    for name in INPUTS:
        data = (BASE/name).read_bytes();(directory/'inputs'/name).write_bytes(data)
        result['inputs'][name] = hashlib.sha256(data).hexdigest()
    fixture = json.loads((BASE/'fixture.json').read_text())
    original = tar_bytes(fixture['file'],fixture['file']['body'].encode('ascii'))
    changed = tar_bytes(fixture['file'],fixture['changedBody'].encode('ascii'))
    (directory/'artifacts/baseline.tar').write_bytes(original)
    (directory/'artifacts/changed.tar').write_bytes(changed)
    a,b = gzip_bytes(original,0),gzip_bytes(original,1)
    header_tamper = bytearray(a);header_tamper[4]=1
    bad_crc = bytearray(a);bad_crc[-8] ^= 1
    blobs = {'mtime0':a,'mtime1':b,'wrong-size':a,'header-tamper':bytes(header_tamper),
             'changed-content':gzip_bytes(changed,0),'truncated':a[:-4],
             'bad-crc':bytes(bad_crc),'trailing':a+b'X','concatenated':a+a}
    for key,blob in blobs.items():
        path = 'artifacts/'+key+'.gz';(directory/path).write_bytes(blob)
        result['assets'][key] = {'file':path,'bytes':len(blob),'digest':digest(blob),
                                 'headerHex':blob[:10].hex(),'mtime':int.from_bytes(blob[4:8],'little')}
    base_descriptor = {'mediaType':MEDIA,'digest':digest(a),'size':len(a)}
    for case in json.loads((BASE/'cases.json').read_text())['cases']:
        blob = blobs[case['variant']]
        descriptor = {'mediaType':MEDIA,'digest':digest(blob),'size':len(blob)}
        if case['variant']=='header-tamper':descriptor = deepcopy(base_descriptor)
        if case['variant']=='wrong-size':descriptor['size'] += 1
        before = deepcopy(descriptor)
        outcome = verify_layer(blob,descriptor,digest(original),case['outputCap'],case['mode'])
        result['cases'].append({**case,'input':{'blobFile':result['assets'][case['variant']]['file'],
             'descriptor':before,'expectedDiffId':digest(original),'outputCap':case['outputCap']},
             'descriptorAfter':descriptor,'outcome':outcome})
    normal0,normal1=[r['outcome'] for r in result['cases'][:2]]
    hex0=normal0['diagnostics'].get('acceptedTarHex');hex1=normal1['diagnostics'].get('acceptedTarHex')
    result['relationships']={'compressedSizesEqual':len(a)==len(b),'compressedDigestsEqual':digest(a)==digest(b),
         'gzipBytesDifferOnlyAt':[i for i,(x,y) in enumerate(zip(a,b)) if x!=y],
         'uncompressedBytesEqual':hex0 is not None and hex0==hex1,
         'diffIdsEqual':normal0['diagnostics']['observedDiffId']==normal1['diagnostics']['observedDiffId'],
         'tarBytes':len(original)}
    result['tar']={'bytes':len(original),'diffId':digest(original),'changedDiffId':digest(changed),
                   'baselineFile':'artifacts/baseline.tar','changedFile':'artifacts/changed.tar'}
    result['elapsedSeconds']=time.monotonic()-start
    result['finishedAt']=datetime.now(timezone.utc).isoformat()
    (directory/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'Atlas':'OCI有限実計算','cases':len(result['cases']),'elapsedSeconds':result['elapsedSeconds'],
                      'actualNice':result['actualNice'],'blobBytes':len(a),'tarBytes':len(original)},ensure_ascii=False))

if __name__=='__main__':main()
