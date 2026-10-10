import copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def oracle(key,message):
    # Independent RFC2104 construction, not hmac library / producer serializer.
    if len(key)>64:key=hashlib.sha256(key).digest()
    key=key.ljust(64,b'\0')
    inner=hashlib.sha256(bytes(x^0x36 for x in key)+message).digest()
    return hashlib.sha256(bytes(x^0x5c for x in key)+inner).hexdigest()
def check_rows(raw,c,e):
    key=bytes.fromhex(c['public_fixture_key_hex']);by={r['id']:r for r in raw['rows']}
    assert len(raw['rows'])==14 and len(by)==14
    literals=e['bytes_ascii']
    def checktrace(t,a,b,equal):
        assert t=={'left_ascii':a,'right_ascii':b,'left_hex':a.encode('ascii').hex(),'right_hex':b.encode('ascii').hex(),'left_tag':oracle(key,a.encode('ascii')),'right_tag':oracle(key,b.encode('ascii')),'bytes_equal':equal,'tags_equal':equal,'original_tag_verifies_changed':equal}
    for s in c['cases']:
        r=by[s['id']]
        left,right=json.loads(s['left']),json.loads(s['right'])
        if s['mode'] in ('raw','canonical'):assert left==right
        else:assert [f for f in c['fields'] if left[f]!=right[f]]==[s['omit']]
        assert r['status']=='accepted' and r['input_left']==s['left'] and r['input_right']==s['right'] and r['mode']==s['mode']
        if s['mode']=='raw':a,b=literals['base'],literals[s['id']];equal=False
        elif s['mode']=='canonical':a=b=literals['base'];equal=True
        else:a,b=literals['base'],literals[s['id']];equal=False
        checktrace(r['normal'],a,b,equal)
        if s['mode']=='context':
            assert r['omitted']==s['omit'];a=b=literals['omit-'+s['omit']];checktrace(r['faulty'],a,b,True)
        else:assert 'faulty' not in r
    for s in c['refusals']:
        r=by[s['id']];assert r=={'id':s['id'],'label':s['label'],'status':'expected-refusal','input':s['input'],'reason':s['reason'],'tags_created':False}
    assert raw['public_key_hex']==c['public_fixture_key_hex']
def main():
    pointer=(ROOT/'observation-data.js').read_text();raw=json.loads(pointer.removeprefix('window.BYTES_OBSERVATION = ').strip().removesuffix(';'))
    d=ROOT/'observations'/raw['run_id'];assert json.loads((d/'raw.json').read_text())==raw
    for n,h in raw['source_digests'].items():assert sha(ROOT/n)==h,n
    for n,v in json.loads((d/'artifact-index.json').read_text())['artifacts'].items():assert sha(d/n)==v['sha256'] and (d/n).stat().st_size==v['bytes']
    c=json.loads((ROOT/'contracts.json').read_text());e=json.loads((ROOT/'expected-bytes.json').read_text())
    for n in ('contracts.json','expected-bytes.json'):assert (ROOT/n).read_bytes()==(d/n).read_bytes()
    cmd=json.loads((d/'command.json').read_text());assert cmd['exit']==0 and cmd['stderr']=='' and cmd['argv']==['python3','calculate.py']
    produced=json.loads(cmd['stdout']);assert produced['rows']==raw['rows'] and produced['public_key_hex']==raw['public_key_hex']
    v=e['rfc4231_case1'];assert oracle(bytes.fromhex(v['key_hex']),v['message_ascii'].encode())==v['tag_hex']
    # Known primary vector constants are anchored independently of fixture file.
    assert v['key_hex']=='0b'*20 and v['message_ascii']=='Hi There' and v['tag_hex']=='b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7'
    check_rows(raw,c,e)
    detected=[]
    for fault in ('raw-semantic-only','canonical-wrong-bytes','context-omitted-hidden','refusal-as-success'):
        bad=copy.deepcopy(raw)
        if fault=='raw-semantic-only':bad['rows'][0]['normal']['original_tag_verifies_changed']=True
        if fault=='canonical-wrong-bytes':bad['rows'][2]['normal']['left_ascii']='{}'
        if fault=='context-omitted-hidden':bad['rows'][3]['faulty']['original_tag_verifies_changed']=False
        if fault=='refusal-as-success':bad['rows'][6]['status']='accepted'
        try:check_rows(bad,c,e)
        except AssertionError:detected.append(fault)
        else:raise AssertionError('negative control escaped '+fault)
    sys.dont_write_bytecode=True
    import route
    for q,target in route.ROUTES.items():assert route.route(q)=={'supported':True,'target':target,'executed':False,'reason':None}
    for q in route.UNSUPPORTED:assert route.route(q)['supported'] is False and route.route(q)['executed'] is False
    print(json.dumps({'status':'passed','run_id':raw['run_id'],'accepted':6,'expected_refusals':8,'rfc4231_vectors':1,'independent_oracle':'fixed literals + hashlib ipad/opad; no producer serializer or hmac import','negative_controls_detected':detected,'skill_routes':{'normal':8,'unsupported':4,'scope':'structural only; model behavior unrun'}}))
if __name__=='__main__':main()
