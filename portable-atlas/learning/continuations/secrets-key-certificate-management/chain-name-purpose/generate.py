"""Explicit generation only; disposable synthetic signing keys never persisted."""
import sys
sys.dont_write_bytecode=True
import datetime,json,tempfile
from pathlib import Path
from tool import ROOT,command,probe
p=probe();history=[]
def run(args):
    r=command(args);assert r['exit']==0,(args,r['stderr']);history.append(r)
ca='basicConstraints=critical,CA:TRUE,pathlen:0\nkeyUsage=critical,keyCertSign,cRLSign\nsubjectKeyIdentifier=hash\nauthorityKeyIdentifier=keyid:always\n'
(ROOT/'profiles').mkdir(exist_ok=True)
(ROOT/'profiles/ca.cnf').write_text(ca)
for name,san,eku in [('good','api.atlas.invalid','serverAuth'),('wrong-san','other.atlas.invalid','serverAuth'),('client','api.atlas.invalid','clientAuth')]:
    (ROOT/('profiles/'+name+'.cnf')).write_text('basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature\nsubjectKeyIdentifier=hash\nauthorityKeyIdentifier=keyid:always\nsubjectAltName=DNS:'+san+'\nextendedKeyUsage='+eku+'\n')
with tempfile.TemporaryDirectory(prefix='.dummykeys-',dir=ROOT) as temp:
    rel=str(Path(temp).relative_to(ROOT))
    for name,serial in [('a','1'),('b','2')]:
        run(['genpkey','-algorithm','EC','-pkeyopt','ec_paramgen_curve:P-256','-out',rel+'/root-'+name+'.key'])
        run(['x509','-new','-key',rel+'/root-'+name+'.key','-subj','/CN=Atlas Dummy Root '+name.upper(),'-set_serial',serial,'-not_before','20260101000000Z','-not_after','20300101000000Z','-extfile','profiles/ca.cnf','-out','certs/root-'+name+'.pem'])
    run(['genpkey','-algorithm','EC','-pkeyopt','ec_paramgen_curve:P-256','-out',rel+'/leaf.key'])
    run(['pkey','-in',rel+'/leaf.key','-pubout','-out',rel+'/leaf.pub'])
    for name,serial in [('good','101'),('wrong-san','102'),('client','103')]:
        run(['x509','-new','-force_pubkey',rel+'/leaf.pub','-CA','certs/root-a.pem','-CAkey',rel+'/root-a.key','-subj','/CN=api.atlas.invalid','-set_serial',serial,'-not_before','20261005000000Z','-not_after','20261006000000Z','-extfile','profiles/'+name+'.cnf','-out','certs/leaf-'+name+'.pem'])
    # Recorded argv retain operation/filename but replace random ephemeral path.
    for row in history:row['argv']=[s.replace(rel,'<ephemeral-dummy>') for s in row['argv']];row['stderr']=row['stderr'].replace(rel,'<ephemeral-dummy>')
assert not list(ROOT.glob('.dummykeys-*'))
(ROOT/'evidence/generation.json').write_text(json.dumps({'recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'probe':p,'dummyOnly':True,'privateKeysPersisted':False,'privateKeyDirectoryRemoved':True,'commands':history},indent=2)+'\n')
print('Generated 2 dummy roots and 3 leaves; ephemeral private keys removed. Public certificates only.')
