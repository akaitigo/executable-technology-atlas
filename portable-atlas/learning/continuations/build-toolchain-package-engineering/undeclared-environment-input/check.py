"""Independent reader; does not import runner or execute compiler/binary."""
import copy,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
SOURCE=b'#include <banner.h>\nextern int puts(const char *);\nint main(void) { return puts(BANNER) < 0; }\n'
def digest(data):return hashlib.sha256(data).hexdigest()
def validate(raw,expected):
    assert bytes.fromhex(raw['inputs']['source_hex'])==SOURCE
    assert raw['compiler']['invoked_path'] in ('/usr/bin/clang','/Library/Developer/CommandLineTools/usr/bin/clang') and 'clang version' in raw['compiler']['version']
    assert raw['cleanup']['owned_temp_removed'] is True
    rows={a['name']:a for a in raw['attempts']};assert list(rows)==list(expected)
    for name,want in expected.items():
        a=rows[name]; assert a['execution']['stdout']==want['stdout'] and a['execution']['exit']==0 and not a['execution']['stderr']
        assert a['cache_hit']==want['hit'];assert (a['compile'] is None)==want['hit']
        letter='A' if name.endswith('-A') else 'B';header=b'#define BANNER "'+letter.encode()+b'"\n'
        assert bytes.fromhex(raw['inputs']['headers_hex'][letter])==header
        assert a['header_sha256']==digest(header) and a['resolved_dependencies']==['main.c','headers/'+letter+'/banner.h']
        manifest={'source_sha256':digest(SOURCE),'compiler':raw['compiler'],'flags':['-std=c11','-O0','-Wall','-Wextra']+(['-isysroot','/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk'] if raw['compiler']['invoked_path']!='/usr/bin/clang' else [])}
        if name.startswith('good'):manifest['resolved_headers']=[{'logical_name':'banner.h','sha256':digest(header)}]
        assert a['key_payload']==manifest
        assert a['key']==digest(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode())
        assert a['execution']['argv']==['./outputs/'+name]
        assert set(a['execution']['env'])=={'PATH','LC_ALL'}
        if a['compile']:
            assert a['compile']['exit']==0 and a['compile']['env']['CPATH']=='headers/'+letter
            assert set(a['compile']['env'])=={'PATH','LC_ALL','TMPDIR','CPATH'}
    assert rows['bad-A']['key']==rows['bad-B']['key']==rows['clean-B']['key']
    assert rows['bad-A']['binary_sha256']==rows['bad-B']['binary_sha256']
    assert rows['good-A']['key']!=rows['good-B']['key']
    assert rows['bad-B']['binary_sha256']!=rows['clean-B']['binary_sha256']
    assert all(c['exit']==0 for c in raw['commands'])
def verify():
    expected=json.loads((ROOT/'oracle.json').read_text());paths=sorted((ROOT/'observations').glob('*/raw.json'));assert paths,'explicit --record evidence missing'
    for path in paths:
        raw=json.loads(path.read_text());validate(raw,expected)
        for a in raw['attempts']:
            binary=(path.parent/(a['name']+'.bin')).read_bytes();assert digest(binary)==a['binary_sha256'] and len(binary)==a['binary_size']
        assert (path.parent/'main.c').read_bytes()==SOURCE
        for letter in ('A','B'):assert (path.parent/('banner-'+letter+'.h')).read_bytes()==b'#define BANNER "'+letter.encode()+b'"\n'
        for name,value in raw['source_binding'].items():
            source=path.parent/'runner-at-execution.py' if name=='runner.py' and (path.parent/'runner-at-execution.py').exists() else ROOT/name
            assert digest(source.read_bytes())==value
    raw=json.loads(paths[-1].read_text());rejected=0
    for kind in ('stdout','hit','header','key','binary'):
        mutant=copy.deepcopy(raw);a=mutant['attempts'][2]
        if kind=='stdout':a['execution']['stdout']='B\n'
        if kind=='hit':a['cache_hit']=False
        if kind=='header':a['header_sha256']='0'*64
        if kind=='key':a['key']='0'*64
        if kind=='binary':a['binary_sha256']='0'*64
        try:validate(mutant,expected)
        except AssertionError:rejected+=1
        else:raise AssertionError('oracle accepted mutation')
    print(json.dumps({'recorded_runs':len(paths),'attempts_per_run':5,'binary_artifacts_per_run':5,'mutants_rejected':rejected,'scope':'real clang CPATH fixture only'}))
if __name__=='__main__':verify()
