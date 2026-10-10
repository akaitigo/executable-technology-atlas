# SPDX-License-Identifier: Apache-2.0
"""Independent RIFF/sample parser and hand/formula deadline oracle. Explicit --record only."""
import argparse,copy,hashlib,json,platform,random,re,struct,sys
from datetime import datetime,timezone
from pathlib import Path
sys.dont_write_bytecode=True
import media,route
HERE=Path(__file__).resolve().parent
SOURCES=['media.py','verify.py','route.py','serve.py','audio.json','fixtures.json','oracle.json','README.md','VERIFICATION.md','index.html','coverage.json','sources.json','skills/atlas-media-codec-streaming/SKILL.md']
def sha(data):return hashlib.sha256(data).hexdigest()
def digest(path):return sha(path.read_bytes())


def manual_wave(data):
    """Parse actual chunks and signed samples without wave module or media decoder."""
    assert data[:4]==b'RIFF' and data[8:12]==b'WAVE'
    riff_size=int.from_bytes(data[4:8],'little');assert riff_size+8==len(data)
    cursor=12;chunks={}
    while cursor<len(data):
        kind=data[cursor:cursor+4].decode('ascii');size=int.from_bytes(data[cursor+4:cursor+8],'little')
        assert kind not in chunks and cursor+8+size<=len(data)
        chunks[kind]=data[cursor+8:cursor+8+size];cursor+=8+size+(size%2)
    assert cursor==len(data) and set(chunks)=={'fmt ','data'}
    fmt=chunks['fmt '];assert len(fmt)==16
    values=[int.from_bytes(fmt[a:b],'little') for a,b in [(0,2),(2,4),(4,8),(8,12),(12,14),(14,16)]]
    tag,channels,rate,byterate,align,bits=values;pcm=chunks['data']
    assert len(pcm)%align==0 and byterate==rate*align and align==channels*bits//8
    samples=[int.from_bytes(pcm[i:i+2],'little',signed=True) for i in range(0,len(pcm),2)] if bits==16 else []
    return dict(file_bytes=len(data),riff_size=riff_size,format_tag=tag,channels=channels,sample_rate=rate,byte_rate=byterate,block_align=align,bits_per_sample=bits,data_bytes=len(pcm),frames=len(pcm)//align,duration_ms=len(pcm)//align*1000/rate,samples=samples,header_hex=data[:44].hex(),pcm_sha256=sha(pcm))


def timeline_formula(f,policy,delay):
    # PTS oracle is an independent direct deadline predicate, not buffer simulation.
    byseq={p['seq']:p for p in f['arrivals']}
    if policy=='pts':return [i if i in byseq and byseq[i]['arrival_ms']<=delay+10*i else None for i in range(4)]
    # Arrival-order oracle: rank eligible unconsumed events by immutable arrival and input index.
    consumed=set();result=[]
    for i in range(4):
        eligible=[(p['arrival_ms'],j,p['seq']) for j,p in enumerate(f['arrivals']) if j not in consumed and p['arrival_ms']<=delay+10*i]
        if not eligible:result.append(None)
        else:_,j,seq=min(eligible);consumed.add(j);result.append(seq)
    return result


def check_trace(f,a,result,expected):
    assert result['played']==expected
    assert len(result['trace'])==4 and len(result['output_samples'])==320
    independent=[];played=[];arrived=set();dropped=[]
    packets={p['seq']:p for p in f['arrivals']}
    for i,row in enumerate(result['trace']):
        now=result['startup_delay_ms']+i*10
        assert row['slot']==i and row['play_at_ms']==now and row['expected_pts_ms']==i*10
        assert not (set(row['arrived'])&arrived);arrived.update(row['arrived'])
        assert arrived=={p['seq'] for p in f['arrivals'] if p['arrival_ms']<=now}
        dropped+=row['dropped_late']
        assert row['underflow']==(expected[i] is None)
        assert row['pts_mismatch']==(expected[i] is not None and expected[i]!=i)
        if expected[i] is None:chunk=[0]*80;assert row['residence_ms'] is None
        else:
            assert packets[expected[i]]['arrival_ms']<=now
            assert expected[i] not in played;played.append(expected[i])
            assert row['residence_ms']==now-packets[expected[i]]['arrival_ms']
            chunk=a['samples'][expected[i]*80:(expected[i]+1)*80]
        assert row['output_samples']==chunk;independent+=chunk
        assert len(row['buffer_before'])<=4 and set(row['buffer_after']).issubset(set(row['buffer_before']))
    assert independent==result['output_samples'] and result['output_matches_source']==(independent==a['samples'])
    assert result['underflows']==sum(x is None for x in expected)
    assert result['pts_mismatches']==sum(x is not None and x!=i for i,x in enumerate(expected))
    assert result['status']==('ORDERED' if expected==[0,1,2,3] else 'IMPAIRED')
    assert result['buffer_peak_packets']==max(len(r['buffer_before']) for r in result['trace'])
    assert result['dropped_late']==dropped
    if result['policy']=='pts':
        final=result['startup_delay_ms']+30
        assert set(dropped)=={p['seq'] for p in f['arrivals'] if p['arrival_ms']<=final and p['arrival_ms']>result['startup_delay_ms']+p['pts_ms']}
    else:assert not dropped
    assert len(played)+len(dropped)+len(result['unplayed_buffer'])+len(result['future_packets'])==len(f['arrivals'])


def execute():
    a=json.loads((HERE/'audio.json').read_text());fixtures=json.loads((HERE/'fixtures.json').read_text());hand=json.loads((HERE/'oracle.json').read_text())
    # Authored input check independent of media packing/validation.
    pattern=[0,8000,16000,8000,0,-8000,-16000,-8000]
    assert a['samples']==[pattern[j%8]+1000*c for c in range(4) for j in range(80)]
    wav=media.encode_wav(a);decoded=media.decode_wav(wav);manual=manual_wave(wav)
    for k,v in hand['wave_header'].items():assert manual[k]==v,(k,manual[k],v)
    assert decoded['samples']==manual['samples']==a['samples'] and decoded['frames']==320
    independent_pcm=b''.join(x.to_bytes(2,'little',signed=True) for x in a['samples'])
    assert wav[44:]==independent_pcm
    runs=[]
    for f in fixtures:
        outcomes={}
        for policy in ('pts','arrival-order'):
            outcomes[policy]={}
            for n,delay in enumerate(hand['delays_ms']):
                result=media.simulate(f,a,policy,delay);expected=hand['hand_timelines'][f['id']][policy][n]
                assert timeline_formula(f,policy,delay)==expected
                check_trace(f,a,result,expected);outcomes[policy][str(delay)]=result
        runs.append(dict(id=f['id'],input=f,policies=outcomes,independent_hand=hand['hand_timelines'][f['id']]))
    randomized=[];rng=random.Random(20261005)
    for i in range(100):
        f=dict(arrivals=[dict(seq=j,pts_ms=j*10,arrival_ms=j*10+rng.randint(0,30)) for j in range(4) if rng.random()>.2])
        rng.shuffle(f['arrivals']);delay=rng.randint(0,40);outcomes={}
        for policy in ('pts','arrival-order'):
            result=media.simulate(f,a,policy,delay);expected=timeline_formula(f,policy,delay);check_trace(f,a,result,expected)
            outcomes[policy]=dict(expected=expected,result=result)
        randomized.append(dict(input=f,delay_ms=delay,policies=outcomes))
    chosen=next(r for r in runs if r['id']=='reordered')
    def output_file(result):return media.encode_wav(dict(a,samples=result['output_samples']))
    badformat=bytearray(wav);badformat[20:22]=(3).to_bytes(2,'little')
    # Valid mono8 PCM WAV is outside this unit's supported subset, not universally invalid.
    pcm8=bytes([128]*320);fmt8=struct.pack('<HHIIHH',1,1,8000,8000,1,8)
    wav8=b'RIFF'+(36+320).to_bytes(4,'little')+b'WAVEfmt '+(16).to_bytes(4,'little')+fmt8+b'data'+(320).to_bytes(4,'little')+pcm8
    wave_errors=[]
    for name,data in [('unknown-format',bytes(badformat)),('truncated-pcm',wav[:-2]),('unsupported-pcm8',wav8),('not-riff',b'not wave')]:
        try:media.decode_wav(data)
        except ValueError as e:wave_errors.append(dict(id=name,bytes=len(data),sha256=sha(data),error=str(e)))
        else:raise AssertionError(name)
    sample_edges=dict(a,samples=[-32768,32767]+[0]*78)
    edge_bytes=media.encode_wav(sample_edges);assert media.decode_wav(edge_bytes)['samples']==manual_wave(edge_bytes)['samples']==sample_edges['samples']
    artifacts={'source.wav':wav,'pts-delay30.wav':output_file(chosen['policies']['pts']['30']),
               'arrival-delay30.wav':output_file(chosen['policies']['arrival-order']['30']),'pts-delay0-underflow.wav':output_file(chosen['policies']['pts']['0']),
               'unknown-format.bin':bytes(badformat),'truncated-pcm.wav':wav[:-2],'unsupported-pcm8.wav':wav8,'sample-boundaries.wav':edge_bytes}
    assert artifacts['source.wav']==artifacts['pts-delay30.wav']
    assert artifacts['source.wav']!=artifacts['arrival-delay30.wav']!=artifacts['pts-delay0-underflow.wav']
    output_wave_observations={}
    for name in ('source.wav','pts-delay30.wav','arrival-delay30.wav','pts-delay0-underflow.wav','sample-boundaries.wav'):
        d=media.decode_wav(artifacts[name]);m=manual_wave(artifacts[name]);assert d['samples']==m['samples']
        output_wave_observations[name]=dict(sha256=sha(artifacts[name]),header={k:v for k,v in m.items() if k!='samples'},decoded_samples=d['samples'])
    invalid=[]
    for name,change in [('format',dict(format='h264')),('bool-rate',dict(sample_rate=True)),('rate',dict(sample_rate=48000)),('empty',dict(samples=[])),('bool-sample',dict(samples=[True]*80)),('large-sample',dict(samples=[32768]*80)),('low-sample',dict(samples=[-32769]*80)),('chunk-zero',dict(chunk_frames=0)),('fractional-cadence',dict(chunk_frames=4)),('partial-chunk',dict(samples=a['samples'][:-1]))]:
        try:media.encode_wav(dict(a,**change))
        except ValueError as e:invalid.append(dict(id=name,error=str(e)))
        else:raise AssertionError(name)
    base=fixtures[0];invalid_packets=[]
    changes=[('duplicate',[base['arrivals'][0]]*2),('outside-seq',[dict(seq=4,pts_ms=40,arrival_ms=40)]),('bad-pts',[dict(seq=1,pts_ms=0,arrival_ms=10)]),('early-arrival',[dict(seq=1,pts_ms=10,arrival_ms=9)]),('bool-arrival',[dict(seq=0,pts_ms=0,arrival_ms=True)]),('too-late',[dict(seq=0,pts_ms=0,arrival_ms=201)]),('fields',[dict(seq=0,pts_ms=0,arrival_ms=0,extra=1)])]
    for name,arrival in changes:
        try:media.simulate(dict(arrivals=arrival),a)
        except ValueError as e:invalid_packets.append(dict(id=name,error=str(e)))
        else:raise AssertionError(name)
    invalid_options=[]
    for name,f,policy,delay in [('fixture',None,'pts',0),('policy',base,'unknown',0),('bool-delay',base,'pts',True),('negative-delay',base,'pts',-1),('over-delay',base,'pts',61)]:
        try:media.simulate(f,a,policy,delay)
        except ValueError as e:invalid_options.append(dict(id=name,error=str(e)))
        else:raise AssertionError(name)
    raw=dict(version=media.VERSION,seed=20261005,audio_sha256=digest(HERE/'audio.json'),fixture_sha256=digest(HERE/'fixtures.json'),oracle_sha256=digest(HERE/'oracle.json'),
             actual_wav=dict(manual_header={k:v for k,v in manual.items() if k!='samples'},wave_decode=decoded,files=output_wave_observations,rejections=wave_errors),runs=runs,randomized=randomized,
             invalid_audio=invalid,invalid_packets=invalid_packets,invalid_options=invalid_options,artifact_bytes_sha256={name:sha(data) for name,data in artifacts.items()},
             author_routing_smoke={'wav':route.route('wav'),'h264':route.route('h264')},scope='Actual WAV bytes/readback separated from finite fixed-arrival buffer simulation. No product compressed codec or live transport/playback timing.')
    return raw,artifacts


def docs_check(record):
    planned={HERE/'observations/raw.json',HERE/'observations/receipt.json',HERE/'observations/source.wav'}
    for f in ('README.md','skills/atlas-media-codec-streaming/SKILL.md'):
        for link in re.findall(r'\]\(([^)]+)\)',(HERE/f).read_text()):
            if not link.startswith(('https:','#')):
                target=((HERE/f).parent/link.split('#')[0]).resolve();assert target.exists() or (record and target in planned),link
    assert all(w in (HERE/'README.md').read_text() for w in ('前提','主要概念','実務判断','限界','原典','未教材'))
    coverage=json.loads((HERE/'coverage.json').read_text());sources=json.loads((HERE/'sources.json').read_text());ids={s['id'] for s in sources}
    assert 2<=len(coverage['next_experiments'])<=4
    for item in coverage['areas']+coverage['next_experiments']:assert item['source'] in ids and item['question']
    assert all(s in (HERE/'index.html').read_text() for s in ('coverage.json','sources.json','README.md'))
    assert route.route('wav')['status']=='supported' and route.route('h264')['status']=='unsupported'


def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');args=p.parse_args()
    raw,artifacts=execute();docs_check(args.record);sources={f:digest(HERE/f) for f in SOURCES};folder=HERE/'observations';qa=json.loads((folder/'ui-qa.json').read_text())
    if qa['status']=='passed':
        for key,file in [('observed_ui_sha256','index.html'),('observed_sources_sha256','sources.json'),('observed_coverage_sha256','coverage.json')]:assert qa[key]==digest(HERE/file)
        browser_wave=qa['actual_wav_browser'];assert browser_wave['sha256']==raw['artifact_bytes_sha256']['source.wav']
        for key,value in browser_wave.items():
            if key in raw['actual_wav']['manual_header']:assert value==raw['actual_wav']['manual_header'][key]
        assert browser_wave['first16_samples']==raw['actual_wav']['wave_decode']['samples'][:16]
        rows=json.loads((folder/'ui-matrix.json').read_text())['rows'];assert len(rows)==36 and len({(r['id'],r['policy'],r['delay_ms']) for r in rows})==36
        for row in rows:
            result=next(r for r in raw['runs'] if r['id']==row['id'])['policies'][row['policy']][str(row['delay_ms'])]
            for key in ('status','underflows','pts_mismatches','played','output_matches_source','buffer_peak_packets'):assert row[key]==result[key]
    if args.record:
        for name,data in artifacts.items():(folder/name).write_bytes(data)
        (folder/'raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
        names=['observations/raw.json','observations/ui-qa.json']+['observations/'+name for name in artifacts]
        for name in ('ui-matrix.json','preview-http.log','default-bind.txt','skill-smoke.json','iteration-failure.txt'):
            if (folder/name).exists():names.append('observations/'+name)
        receipt=dict(executed_at_utc=datetime.now(timezone.utc).isoformat(),command='python3 verify.py --record',environment=dict(python=platform.python_version(),system=platform.system(),machine=platform.machine()),inputs=dict(audio=raw['audio_sha256'],fixtures=raw['fixture_sha256'],oracle=raw['oracle_sha256']),sources=sources,artifacts={f:digest(HERE/f) for f in names},checks=dict(actual_wave_bytes_readback='passed; manual header/sample oracle',hand_timeline_and_random='passed',roadmap_local_links_sources='passed',author_smoke='passed; not independent AgentEval',actual_iab_qa=qa['status']))
        (folder/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    else:
        receipt=json.loads((folder/'receipt.json').read_text());assert receipt['sources']==sources,'changed sources require explicit --record'
        assert receipt['inputs']==dict(audio=raw['audio_sha256'],fixtures=raw['fixture_sha256'],oracle=raw['oracle_sha256'])
        for f,h in receipt['artifacts'].items():assert digest(HERE/f)==h,f
        for name,data in artifacts.items():assert (folder/name).read_bytes()==data,name
        assert raw==json.loads((folder/'raw.json').read_text())
        if qa.get('observed_raw_sha256'):assert qa['observed_raw_sha256']==digest(folder/'raw.json')
    print(json.dumps(dict(status='passed',record=args.record,actual_wav_frames=320,wav_bytes=684,scenarios=6,policies=2,delays=3,random_timelines=100,invalid_audio=10,invalid_packets=7,invalid_options=5,wav_rejections=4)))
if __name__=='__main__':main()
