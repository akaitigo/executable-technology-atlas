"""Hand-authored token oracle. Does not import model or parse Exec text."""
TOKENS={
 'quoted':[('atlas-viewer',False),('--label=two words',True),('%F',False)],
 'single':[('atlas-viewer',False),('%f',False)],
 'percent':[('atlas-viewer',False),('--progress=100%%',False),('%F',False)],
 'plain':[('atlas-viewer',False),('--read-only',False),('%F',False)],
 'empty-arg':[('atlas-viewer',False),('',True),('%F',False)],
 'dollar':[('atlas-viewer',False),('cost$5',True),('%F',False)],
 'backslash':[('atlas-viewer',False),('C:\\box',True),('%F',False)],
 'quote':[('atlas-viewer',False),('say"hello"',True),('%F',False)],
 'backtick':[('atlas-viewer',False),('tick`name',True),('%F',False)],
 'quoted-executable':[('/synthetic/My Apps/atlas-viewer',True),('%F',False)],
 'literal-metachar':[('atlas-viewer',False),('semi;pipe|literal',True),('%F',False)],
 'no-field':[('atlas-viewer',False),('--read-only',False)]}
REJECT={'unknown':'invalid','duplicate-field':'invalid','quoted-field':'unsupported','embedded-field':'unsupported','unclosed':'invalid','partial-quote':'invalid','unquoted-shell':'invalid','shell-program':'policy','known-url':'unsupported','bad-escape':'invalid','duplicate-key':'invalid','dbus':'unsupported','terminal':'unsupported','missing-exec':'invalid','wrong-type':'unsupported'}
FILES={'none':[],'one':['/synthetic/a.txt'],'spaces':['/synthetic/two words.txt','/synthetic/b.txt'],'percent-name':['/synthetic/%F.txt'],'max':['/synthetic/a.txt','/synthetic/日本語.txt','/synthetic/c.txt']}
def expected(case,selection,launch='argv-model'):
    if launch!='argv-model':return {'status':'rejected','kind':'policy','tokens':None,'argvModels':[],'spawned':False,'shell':False}
    if case in REJECT:return {'status':'rejected','kind':REJECT[case],'tokens':None,'argvModels':[],'spawned':False,'shell':False}
    tokens=TOKENS[case];files=FILES[selection];fixed=[v.replace('%%','%') for v,_ in tokens if v not in ('%f','%F')]
    field=next((v for v,_ in tokens if v in ('%f','%F')),None)
    # All hand fixtures place file code last. One model per file for %f is a teaching policy.
    argv=[fixed+[f] for f in files] if field=='%f' and files else [fixed+(files if field else [])]
    return {'status':'modeled','kind':None,'tokens':[{'value':v,'quoted':q} for v,q in tokens],'argvModels':argv,'spawned':False,'shell':False}
