# SPDX-License-Identifier: Apache-2.0
"""Exact Fraction component oracle and immutable bit/error vectors. Explicit --record only."""
import argparse,copy,hashlib,json,math,platform,random,re,sys
from datetime import datetime,timezone
from fractions import Fraction
from pathlib import Path
sys.dont_write_bytecode=True
import bpsk,route
HERE=Path(__file__).resolve().parent
SOURCES=['bpsk.py','verify.py','route.py','serve.py','base.json','fixtures.json','oracle.json','README.md','VERIFICATION.md','index.html','coverage.json','sources.json','skills/atlas-telecom-sdr/SKILL.md']
AXES={0:(1,0),90:(0,1),180:(-1,0),270:(0,-1)}
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def frac(v):return Fraction(str(v))
def close(a,b):assert math.isclose(a,float(b),rel_tol=1e-12,abs_tol=1e-12),(a,b)


def component_oracle(base,f,mode,known_axis):
    # No complex multiplication, trig, bpsk validation/modulation/estimation/demodulation calls.
    u,v=AXES[f['phase_deg']];gain=frac(f['gain']);received=[]
    for bit,(nr,ni) in zip(base['bits'],f['noise']):
        sign=1 if bit==0 else -1
        received.append((sign*gain*u+frac(nr),sign*gain*v+frac(ni)))
    pilot=[]
    for bit,(nr,ni) in zip(base['pilot_bits'],f['pilot_noise']):
        sign=1 if bit==0 else -1;pilot.append((sign*gain*u+frac(nr),sign*gain*v+frac(ni)))
    count=len(pilot)
    estimate=tuple(sum((1 if bit==0 else -1)*p[k] for bit,p in zip(base['pilot_bits'],pilot))/count for k in (0,1))
    if known_axis is None:assert estimate==(0,0)
    else:
        a,b=known_axis;assert estimate[0]*b==estimate[1]*a and estimate[0]*a+estimate[1]*b>0
    axis=(1,0) if mode=='none' else known_axis
    if axis is None:return received,pilot,estimate,None,None
    a,b=axis;decisions=[(r*a+i*b,i*a-r*b) for r,i in received]
    decoded=[1 if r<0 else 0 for r,i in decisions]
    return received,pilot,estimate,decisions,decoded


def check(base,f,result,axis,hand=None):
    received,pilot,estimate,decisions,decoded=component_oracle(base,f,result['mode'],axis)
    assert result['decoded_bits']==decoded
    errors=[i for i,bit in enumerate(decoded) if bit!=base['bits'][i]] if decoded is not None else None
    if hand is not None:
        assert decoded==hand[result['mode']] and errors==hand[result['mode']+'_errors']
    assert result['error_indices']==errors
    assert result['error_count']==(len(errors) if errors is not None else None)
    assert result['compared_bits']==(len(base['bits']) if decoded is not None else 0)
    assert result['ber']==(len(errors)/len(base['bits']) if errors is not None else None)
    assert result['status']==('NO_PHASE_ESTIMATE' if decoded is None else ('BIT_ERRORS' if errors else 'MATCH'))
    assert result['pilot_phase_available']==(axis is not None)
    for k in (0,1):close(result['pilot_estimate'][k],estimate[k])
    sps=base['samples_per_symbol'];n=len(base['bits'])
    assert result['payload_sample_count']==n*sps and result['sample_rate']==base['symbol_rate']*sps
    close(result['payload_duration_ms'],Fraction(n*1000,base['symbol_rate']))
    for i,point in enumerate(result['received_samples']):
        for k in (0,1):close(point[k],received[i//sps][k])
    for i,point in enumerate(result['pilot_received_samples']):
        for k in (0,1):close(point[k],pilot[i//sps][k])
    for i,point in enumerate(result['transmit_samples']):assert point==[1 if base['bits'][i//sps]==0 else -1,0]
    for i,row in enumerate(result['trace']):
        assert row['index']==i and row['input_bit']==base['bits'][i] and row['sample_range']==[i*sps,(i+1)*sps]
        for k in (0,1):close(row['received_symbol'][k],received[i][k])
        if decisions is None:
            assert row['decision_symbol'] is row['decoded_bit'] is row['hard_tie'] is row['incorrect'] is None
        else:
            for k in (0,1):close(row['decision_symbol'][k],decisions[i][k])
            assert row['decoded_bit']==decoded[i] and row['hard_tie']==(decisions[i][0]==0) and row['incorrect']==(i in errors)
    if decisions is None:assert result['decision_samples'] is None
    else:
        for i,point in enumerate(result['decision_samples']):
            for k in (0,1):close(point[k],decisions[i//sps][k])
    if result['mode']=='pilot' and axis is not None:
        for k in (0,1):close(result['correction_factor'][k],axis[k] if k==0 else -axis[k])


def execute():
    base=json.loads((HERE/'base.json').read_text());fixtures=json.loads((HERE/'fixtures.json').read_text());hand=json.loads((HERE/'oracle.json').read_text())['hand_cases']
    assert base['bits']==[0,1,1,0,1,0,0,1,0,0,1,1,0,1,1,0] and base['pilot_bits']==[0,1,0,1]
    assert {f['id'] for f in fixtures}==set(hand)
    runs=[]
    for f in fixtures:
        outcomes={}
        for mode in ('none','pilot'):
            result=bpsk.execute(base,f,mode);check(base,f,result,hand[f['id']]['axis'],hand[f['id']]);outcomes[mode]=result
        runs.append(dict(id=f['id'],input=f,independent_hand=hand[f['id']],policies=outcomes))
    rng=random.Random(20261005);randomized=[]
    for i in range(100):
        bits=[rng.randrange(2) for _ in range(16)];test=dict(base,bits=bits,samples_per_symbol=rng.randint(1,8))
        phase=rng.choice([0,90,180,270]);gain=rng.choice([.5,1,2])
        noise=[[rng.randint(-4,4)/10,rng.randint(-4,4)/10] for _ in bits]
        f=dict(phase_deg=phase,gain=gain,noise=noise,pilot_noise=[[0,0]]*4)
        outcomes={}
        for mode in ('none','pilot'):
            result=bpsk.execute(test,f,mode);check(test,f,result,AXES[phase]);outcomes[mode]=result
        # Rectangular samples/noise are held across the symbol, so ideal average should be sps invariant.
        one=bpsk.execute(dict(test,samples_per_symbol=1),f,'pilot');assert one['decoded_bits']==outcomes['pilot']['decoded_bits']
        randomized.append(dict(base=test,input=f,axis=list(AXES[phase]),policies=outcomes))
    invalid=[];f=fixtures[0]
    cases=[('empty-bits',dict(bits=[]),{}),('nonbinary',dict(bits=[2]),{}),('bool-bit',dict(bits=[True]),{}),('pilot-short',dict(pilot_bits=[0]),{}),('sps-zero',dict(samples_per_symbol=0),{}),('sps-bool',dict(samples_per_symbol=True),{}),('sps-large',dict(samples_per_symbol=17),{}),('rate-zero',dict(symbol_rate=0),{}),('rate-bool',dict(symbol_rate=True),{}),('phase45',{},dict(phase_deg=45)),('phase-bool',{},dict(phase_deg=True)),('gain-negative',{},dict(gain=-1)),('gain-high',{},dict(gain=3)),('gain-bool',{},dict(gain=True)),('noise-short',{},dict(noise=[])),('noise-bool',{},dict(noise=[[True,0]]*16)),('noise-high',{},dict(noise=[[5,0]]*16)),('pilot-noise-short',{},dict(pilot_noise=[]))]
    for name,base_change,fixture_change in cases:
        try:bpsk.execute(dict(base,**base_change),dict(f,**fixture_change))
        except ValueError as e:invalid.append(dict(id=name,error=str(e)))
        else:raise AssertionError(name)
    nonfinite=[]
    for name,value in [('nan',float('nan')),('infinity',float('inf'))]:
        for field in ['gain','noise']:
            change={field:value} if field=='gain' else {'noise':[[value,0]]*16}
            try:bpsk.execute(base,dict(f,**change))
            except ValueError as e:nonfinite.append(dict(id=name+'-'+field,error=str(e),input_description=name+' (JSON non-finite values not serialized)'))
            else:raise AssertionError(name+field)
    options=[]
    for name,b,fixture,mode in [('base-object',None,f,'pilot'),('fixture-object',base,None,'pilot'),('mode',base,f,'unknown')]:
        try:bpsk.execute(b,fixture,mode)
        except ValueError as e:options.append(dict(id=name,error=str(e)))
        else:raise AssertionError(name)
    raw=dict(version=bpsk.VERSION,seed=20261005,base=base,base_sha256=digest(HERE/'base.json'),fixtures_sha256=digest(HERE/'fixtures.json'),oracle_sha256=digest(HERE/'oracle.json'),runs=runs,randomized=randomized,invalid_inputs=invalid,nonfinite_rejections=nonfinite,invalid_options=options,
             author_routing_smoke={'bpsk':route.route('bpsk'),'rf-transmit':route.route('rf-transmit')},scope='Calculated complex baseband samples, exact quadrants and symbol-held authored noise. BER counts payload bits only; no statistical channel estimate, hardware/RF/standard conformance.')
    selected=next(r for r in runs if r['id']=='fixed-noise-90')['policies']['pilot']
    iq_artifact=dict(format='JSON I/Q pairs of computed Python complex samples, no device format or capture',case='fixed-noise-90',payload_received=selected['received_samples'],payload_corrected=selected['decision_samples'],pilot_received=selected['pilot_received_samples'],sample_rate=selected['sample_rate'])
    return raw,iq_artifact


def docs_check(record):
    planned={HERE/'observations/raw.json',HERE/'observations/receipt.json',HERE/'observations/complex-samples.json'}
    for f in ('README.md','skills/atlas-telecom-sdr/SKILL.md'):
        for link in re.findall(r'\]\(([^)]+)\)',(HERE/f).read_text()):
            if not link.startswith(('https:','#')):
                target=((HERE/f).parent/link.split('#')[0]).resolve();assert target.exists() or (record and target in planned),link
    assert all(w in (HERE/'README.md').read_text() for w in ('前提','主要概念','実務判断','限界','原典','未教材'))
    coverage=json.loads((HERE/'coverage.json').read_text());sources=json.loads((HERE/'sources.json').read_text());ids={s['id'] for s in sources}
    assert 2<=len(coverage['next_experiments'])<=4
    for a in coverage['areas']+coverage['next_experiments']:assert a['source'] in ids and a['question']
    assert all(s in (HERE/'index.html').read_text() for s in ('coverage.json','sources.json','README.md'))
    assert route.route('bpsk')['status']=='supported' and route.route('rf-transmit')['status']=='unsupported'


def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');args=p.parse_args()
    raw,iq=execute();docs_check(args.record);folder=HERE/'observations';sources={f:digest(HERE/f) for f in SOURCES};qa=json.loads((folder/'ui-qa.json').read_text())
    if qa['status']=='passed':
        for key,file in [('observed_ui_sha256','index.html'),('observed_sources_sha256','sources.json'),('observed_coverage_sha256','coverage.json')]:assert qa[key]==digest(HERE/file)
        rows=json.loads((folder/'ui-matrix.json').read_text())['rows'];assert len(rows)==22 and len({(r['id'],r['mode']) for r in rows})==22
        for row in rows:
            result=next(r for r in raw['runs'] if r['id']==row['id'])['policies'][row['mode']]
            for key in ('status','error_count','compared_bits','ber','decoded_bits','pilot_phase_available'):assert row[key]==result[key]
    if args.record:
        (folder/'raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
        (folder/'complex-samples.json').write_text(json.dumps(iq,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
        names=['observations/raw.json','observations/complex-samples.json','observations/ui-qa.json']
        for name in ('ui-matrix.json','preview-http.log','default-bind.txt','skill-smoke.json','iteration-failure.txt'):
            if (folder/name).exists():names.append('observations/'+name)
        receipt=dict(executed_at_utc=datetime.now(timezone.utc).isoformat(),command='python3 verify.py --record',environment=dict(python=platform.python_version(),system=platform.system(),machine=platform.machine()),inputs=dict(base=raw['base_sha256'],fixtures=raw['fixtures_sha256'],oracle=raw['oracle_sha256']),sources=sources,artifacts={f:digest(HERE/f) for f in names},checks=dict(exact_component_bit_ber_oracle='passed',roadmap_local_links_binding='passed',author_smoke='passed; not independent AgentEval',actual_iab_qa=qa['status']))
        (folder/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    else:
        receipt=json.loads((folder/'receipt.json').read_text());assert receipt['sources']==sources,'changed sources require explicit --record'
        assert receipt['inputs']==dict(base=raw['base_sha256'],fixtures=raw['fixtures_sha256'],oracle=raw['oracle_sha256'])
        for f,h in receipt['artifacts'].items():assert digest(HERE/f)==h,f
        assert raw==json.loads((folder/'raw.json').read_text()) and iq==json.loads((folder/'complex-samples.json').read_text())
        if qa.get('observed_raw_sha256'):assert qa['observed_raw_sha256']==digest(folder/'raw.json')
    print(json.dumps(dict(status='passed',record=args.record,cases=11,policies=2,payload_bits=16,payload_complex_samples=64,pilot_complex_samples=16,random_vectors=100,invalid_inputs=18,nonfinite_rejections=4,invalid_options=3)))
if __name__=='__main__':main()
