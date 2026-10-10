"""Python stdlib only; default is read-only. --record must name a new directory."""
import argparse, datetime, hashlib, json, pathlib, platform, re, sys

ROOT = pathlib.Path(__file__).resolve().parent

def validate(value):
    error = 'not-string' if not isinstance(value, str) else 'unpaired-surrogate' if any(0xd800 <= ord(c) <= 0xdfff for c in value) else None
    if error:
        return dict(error=error, codePoints=None, utf16Units=None, utf8Bytes=None, legacyAccepted=False, codePointAccepted=False, byteAccepted=False)
    cp = len(value)
    return dict(error=None, codePoints=cp, utf16Units=len(value.encode('utf-16-le'))//2,
                utf8Bytes=len(value.encode('utf-8')), legacyAccepted=1<=cp<=4,
                codePointAccepted=1<=cp<=4, byteAccepted=1<=len(value.encode('utf-8'))<=8)

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--record')
    args = parser.parse_args()
    destination = None
    if args.record:
        destination = ROOT / args.record
        if not re.fullmatch(r'observations/[a-z0-9-]+', args.record) or destination.exists():
            parser.error('record needs an unused observations/name directory')
    started = now()
    fixtures = json.loads((ROOT/'vectors.json').read_text())
    oracle = json.loads((ROOT/'oracle.json').read_text())['scalars']
    results = []
    checks = 0
    for vector in fixtures:
        result = validate(vector['input'])
        p = oracle[vector['id']]
        if p is not None:
            # Independent fixed scalar list also establishes exact input identity.
            assert vector['input'] == ''.join(chr(v) for v in p)
            cp = len(p)
            u = sum(2 if v>65535 else 1 for v in p)
            b = sum(1 if v<128 else 2 if v<2048 else 3 if v<65536 else 4 for v in p)
            expected = dict(error=None,codePoints=cp,utf16Units=u,utf8Bytes=b,legacyAccepted=1<=cp<=4,codePointAccepted=1<=cp<=4,byteAccepted=1<=b<=8)
        else:
            expected = dict(error='not-string' if vector['id']=='not-string' else 'unpaired-surrogate',codePoints=None,utf16Units=None,utf8Bytes=None,legacyAccepted=False,codePointAccepted=False,byteAccepted=False)
        assert result == expected, vector['id']
        checks += len(expected)
        results.append(dict(id=vector['id'],input=vector['input'],result=result))
    # source membership is fixed in sources.mjs, not glob-dependent.
    source_names = json.loads('['+(ROOT/'sources.mjs').read_text().split('[',1)[1].rsplit(']',1)[0].replace("'",'"')+']')
    hashes = {f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in source_names}
    raw = dict(kind='actual-python-stdlib',started=started,completed=now(),command='python3 -B verify.py'+(' --record '+args.record if args.record else ''),attempt=1,retries=0,
               environment=dict(implementation=platform.python_implementation(),version=platform.python_version(),system=platform.system(),machine=platform.machine()),
               sourceHashes=hashes,inputDigest=hashes['vectors.json'],results=results,checks=checks)
    if destination:
        destination.mkdir(parents=True, exist_ok=False)
        with (destination/'raw.json').open('x') as f: json.dump(raw,f,ensure_ascii=True,indent=2);f.write('\n')
    print(json.dumps(raw,ensure_ascii=True))

if __name__=='__main__': main()
