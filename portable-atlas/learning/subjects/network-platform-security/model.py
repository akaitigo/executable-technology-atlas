"""合成IPv4 packetだけのstateless terminal-rule matcher。"""
import hashlib,ipaddress,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCES={
 'rule-order':'https://netfilter.org/projects/nftables/manpage.html',
 'ipv4':'https://docs.python.org/3/library/ipaddress.html#ipaddress.IPv4Address',
 'private-range':'https://www.rfc-editor.org/rfc/rfc1918.html#section-3'
}
def canonical(o):return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def digest(o):return hashlib.sha256(canonical(o).encode()).hexdigest()
def packet(source,protocol,port):
    if not isinstance(source,str):raise ValueError('source must be IPv4 string')
    try: address=ipaddress.IPv4Address(source)
    except ipaddress.AddressValueError:raise ValueError('malformed or unsupported IPv4 address')
    if protocol not in ('tcp','udp'):raise ValueError('unsupported protocol')
    if type(port) is not int or not 0<=port<=65535:raise ValueError('port must be integer 0..65535')
    return {'source':str(address),'protocol':protocol,'port':port}
def validate_rules(rules):
    if type(rules) is not list or not 1<=len(rules)<=8:raise ValueError('rule count')
    seen=set()
    for r in rules:
        if type(r) is not dict or set(r)!={'id','action','source','protocol','ports'}:raise ValueError('rule schema')
        if not isinstance(r['id'],str) or not r['id'] or r['id'] in seen:raise ValueError('rule id')
        seen.add(r['id'])
        if r['action'] not in ('allow','deny') or r['protocol'] not in ('tcp','udp','any'):raise ValueError('rule action/protocol')
        try:ipaddress.IPv4Network(r['source'],strict=True)
        except (ValueError,TypeError):raise ValueError('rule canonical IPv4 CIDR')
        ps=r['ports']
        if type(ps) is not list or len(ps)!=2 or any(type(x)is not int for x in ps) or not 0<=ps[0]<=ps[1]<=65535:raise ValueError('rule port interval')
def evaluate(p,rules,mode):
    p=packet(p['source'],p['protocol'],p['port']);validate_rules(rules)
    if mode not in ('first-match','naive-any-allow'):raise ValueError('unsupported matcher')
    trace=[];decision='deny';winner='default-deny'
    for i,r in enumerate(rules):
        checks={'source':ipaddress.IPv4Address(p['source']) in ipaddress.IPv4Network(r['source']), 'protocol':r['protocol']=='any' or r['protocol']==p['protocol'],'port':r['ports'][0]<=p['port']<=r['ports'][1]}
        match=all(checks.values()); terminal=match and (mode=='first-match' or r['action']=='allow')
        trace.append({'index':i,'ruleId':r['id'],'action':r['action'],'checks':checks,'matched':match,'terminal':terminal,'effect':'terminal' if terminal else 'deny ignored by naive matcher' if match else 'continue'})
        if terminal:decision=r['action'];winner=r['id'];break
    return {'mode':mode,'decision':decision,'winner':winner,'trace':trace,'traceSha256':digest(trace)}
def experiment(source='10.0.0.130',protocol='tcp',port=443,order='deny-first'):
    p=packet(source,protocol,port)
    rules=json.loads((ROOT/'rules.json').read_text())
    if order=='allow-first':rules=[rules[1],rules[0],*rules[2:]]
    elif order!='deny-first':raise ValueError('unsupported order')
    first=evaluate(p,rules,'first-match');naive=evaluate(p,rules,'naive-any-allow')
    return {'input':{'packet':p,'order':order},'rules':rules,'rulesSha256':digest(rules),'first':first,'naive':naive,'bypass':first['decision']=='deny' and naive['decision']=='allow'}
