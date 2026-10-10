"""Read-only literal expectations independent of observer and consumer prototypes."""
import copy
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parent
# Fixed before first socket run. No import of observer/policies/runner.
HAND={
 'two-datagrams': (['50494e47','48454c4c4f'],[64,64,64],['50494e47','48454c4c4f',None],['50494e47','48454c4c4f'],'50494e4748454c4c4f'),
 'empty-datagram': (['','4e455854'],[64,64,64],['','4e455854',None],[],'4e455854'),
 'small-buffer': (['4142434445464748494a','4e455854'],[3,64,64],['414243','4e455854',None],['414243','4e455854'],'4142434e455854'),
 'exact-fit': (['414243','4e455854'],[3,64,64],['414243','4e455854',None],['414243','4e455854'],'4142434e455854'),
}

def inspect(raw,contracts):
    issues=[]
    if raw['environment']['os']!='Darwin':issues.append('This saved expectation is Mac-specific')
    if len(raw['cases'])!=4 or {c['id'] for c in raw['cases']}!=set(HAND):issues.append('case denominator')
    if raw['attempts']!=1 or raw['retries']!=0 or raw['timeout_seconds']!=0.3:issues.append('bounded attempts')
    inputs={c['id']:c for c in contracts['cases']}
    for case in raw['cases']:
        name=case['id']; sent,widths,expected,eof,joined=HAND[name]
        contract=inputs[name]
        if (contract['sent_hex'],contract['recv_widths'],contract['expected_hex'])!=(sent,widths,expected):issues.append(name+': independent input contract')
        if case['status']!='observed':issues.append(name+': incomplete observation');continue
        times=[datetime.fromisoformat(event['at']) for event in case['events']]
        if times!=sorted(times) or not (datetime.fromisoformat(case['started_at'])<=times[0]<=times[-1]<=datetime.fromisoformat(case['ended_at'])):issues.append(name+': UTC ordering')
        for address in (case['receiver'],case['sender']):
            if address[0]!='127.0.0.1' or not isinstance(address[1],int) or not 1<=address[1]<=65535:issues.append(name+': dynamic loopback endpoint')
        if case['receiver']==case['sender']:issues.append(name+': same endpoint')
        calls=[e for e in case['events'] if e['kind']=='sendto-call']
        returns=[e for e in case['events'] if e['kind']=='sendto-return']
        if len(calls)!=2 or len(returns)!=2:issues.append(name+': send denominator')
        for number,(call,ret,payload) in enumerate(zip(calls,returns,sent),1):
            if call['number']!=number or call['payload_hex']!=payload or call['byte_count']!=len(bytes.fromhex(payload)) or call['destination']!=case['receiver'] or ret['returned_bytes']!=len(bytes.fromhex(payload)) or ret['number']!=number or ret['business_ack'] is not False:issues.append(name+': literal send / no ack')
        receives=[e for e in case['events'] if e['kind']=='recvfrom-call']
        outcomes=[e for e in case['events'] if e['kind'] in ('recvfrom-return','recvfrom-timeout')]
        if [e['bufsize'] for e in receives]!=widths or len(outcomes)!=3:issues.append(name+': receive denominator')
        if max(e['at'] for e in returns)>min(e['at'] for e in receives):issues.append(name+': send before receive')
        if [e['kind'] for e in case['events']]!=['bind','bind','sendto-call','sendto-return','sendto-call','sendto-return','recvfrom-call','recvfrom-return','recvfrom-call','recvfrom-return','recvfrom-call','recvfrom-timeout','close','close']:issues.append(name+': actual call/return order')
        for number,(call,outcome,want) in enumerate(zip(receives,outcomes,expected),1):
            if call['flags']!=0 or call['number']!=number or outcome['number']!=number or outcome['elapsed_ns']<0:issues.append(name+': API call fields')
            if want is None:
                if outcome['kind']!='recvfrom-timeout' or outcome['message']!='timed out' or outcome['exception'] not in ('timeout','TimeoutError'):issues.append(name+': timeout is not EOF/data')
            elif outcome['kind']!='recvfrom-return' or outcome['payload_hex']!=want or outcome['sender']!=case['sender'] or outcome['byte_count']!=len(bytes.fromhex(want)):issues.append(name+': literal payload/sender')
        p=case['consumer_prototypes']
        if p['datagram_candidates']!=expected[:2] or p['tcp_eof_fault']!=eof or p['stream_join_fault']!=joined:issues.append(name+': faulty prototype comparison')
        if case['cleanup']!={'created':2,'closed':2,'open_owned_sockets':0,'owned_threads':0,'method':'same-thread finite calls; finally close'} or any(e['fileno_after_close']!=-1 for e in case['events'] if e['kind']=='close'):issues.append(name+': owned cleanup')
    return issues

def main():
    text=(ROOT/'observation-data.js').read_text()
    payload=json.loads(text.removeprefix('window.UDP_OBSERVATION = ').rstrip().removesuffix(';'))
    folder=ROOT/'observations'/payload['run_id'];manifest=json.loads((folder/'manifest.json').read_text())
    for name,digest in manifest['source_digests'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,'source binding '+name
    for name,info in manifest['artifacts'].items():
        path=folder/name;assert path.stat().st_size==info['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest()==info['sha256'],'artifact '+name
    raw=json.loads((folder/'raw.json').read_text());contract=json.loads((folder/'contracts.json').read_text());command=json.loads((folder/'command.json').read_text())
    assert payload['raw']==raw and payload['contracts']==contract and payload['source_digests']==manifest['source_digests'],'UI/raw/input binding'
    assert json.loads(command['stdout'])==raw and command['exit']==0 and command['stderr']=='','command stdout binding'
    assert not inspect(raw,contract),inspect(raw,contract)
    negatives=[]
    for label in ('lost-tail','wrong-sender','empty-as-eof','no-timeout'):
        bad=copy.deepcopy(raw)
        if label=='lost-tail':bad['cases'][2]['events'][9]['payload_hex']='4445464748494a'
        elif label=='wrong-sender':bad['cases'][0]['events'][7]['sender'][1]+=1
        elif label=='empty-as-eof':bad['cases'][1]['consumer_prototypes']['datagram_candidates']=[]
        else:bad['cases'][0]['events'][11]['kind']='recvfrom-return'
        try:issues=inspect(bad,contract)
        except (KeyError,TypeError):issues=['invalid malformed outcome']
        assert issues,label+' negative control was accepted';negatives.append(label)
    from route import route,ROUTES,UNSUPPORTED
    assert all(route(q)=={'supported':True,'target':t,'network_executed':False} for q,t in ROUTES.items())
    assert all(route(q)['supported'] is False and route(q)['network_executed'] is False for q in UNSUPPORTED)
    skill=ROOT/'skills/atlas-udp-message-boundaries/SKILL.md'
    for target in re.findall(r'\]\(([^)]+)\)',skill.read_text()):assert (skill.parent/target).resolve().is_file(),target
    print(json.dumps({'cases':4,'matches':True,'independent_literal_contract':True,'negative_controls':negatives,'skill_routes':{'normal':len(ROUTES),'unsupported':len(UNSUPPORTED),'structural_only':True},'read_only':True,'binding':True},ensure_ascii=False))

if __name__=='__main__':main()
