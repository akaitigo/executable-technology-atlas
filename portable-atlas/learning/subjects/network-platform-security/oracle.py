"""独立permissions matrix。model/ipaddressはimportしない。"""
# rows: source region; cols: tcp22, tcp443, udp53, other.
DENY_FIRST={'trusted-low':('allow','allow','allow','deny'),'quarantine-high':('deny','deny','deny','deny'),'outside':('deny','deny','deny','deny')}
ALLOW_FIRST={'trusted-low':('allow','allow','allow','deny'),'quarantine-high':('deny','allow','deny','deny'),'outside':('deny','deny','deny','deny')}
NAIVE={'trusted-low':('allow','allow','allow','deny'),'quarantine-high':('deny','allow','deny','deny'),'outside':('deny','deny','deny','deny')}
LOCATORS={
 'rule-order':'https://netfilter.org/projects/nftables/manpage.html',
 'ipv4':'https://docs.python.org/3/library/ipaddress.html#ipaddress.IPv4Address',
 'private-range':'https://www.rfc-editor.org/rfc/rfc1918.html#section-3'
}
def expected(p,order):
    parts=tuple(int(x) for x in p['source'].split('.'))
    region='outside' if parts[:3]!=(10,0,0) else 'trusted-low' if parts[3]<128 else 'quarantine-high'
    col={('tcp',22):0,('tcp',443):1,('udp',53):2}.get((p['protocol'],p['port']),3)
    first=(DENY_FIRST if order=='deny-first' else ALLOW_FIRST)[region][col];naive=NAIVE[region][col]
    return {'region':region,'permissionColumn':col,'first':first,'naive':naive,'bypass':first=='deny' and naive=='allow'}
HAND=[
 ('10.0.0.0','tcp',443,'deny-first','allow','allow'),
 ('10.0.0.127','tcp',22,'deny-first','allow','allow'),
 ('10.0.0.128','tcp',443,'deny-first','deny','allow'),
 ('10.0.0.255','tcp',443,'deny-first','deny','allow'),
 ('10.0.1.0','tcp',443,'deny-first','deny','deny'),
 ('10.0.0.130','tcp',443,'allow-first','allow','allow'),
 ('10.0.0.1','udp',53,'deny-first','allow','allow'),
 ('10.0.0.1','tcp',53,'deny-first','deny','deny'),
 ('10.0.0.1','tcp',0,'deny-first','deny','deny'),
 ('10.0.0.1','tcp',65535,'deny-first','deny','deny')]
