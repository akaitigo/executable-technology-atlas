import hashlib,json
from tool import ROOT,command,probe
# Runner case definitions are separate from oracle's expected conditions.
CASES={'normal':('good','a',1791201600),'wrong-san':('wrong-san','a',1791201600),'untrusted':('good','b',1791201600),'wrong-eku':('client','a',1791201600),'before-start':('good','a',1791158399),'at-start':('good','a',1791158400),'before-end':('good','a',1791244799),'at-end':('good','a',1791244800),'after-end':('good','a',1791244801)}
SOURCES={'verify':'https://docs.openssl.org/3.6/man1/openssl-verification-options/','identity':'https://www.rfc-editor.org/rfc/rfc9525.html','path':'https://www.rfc-editor.org/rfc/rfc5280.html','time':'https://docs.openssl.org/3.6/man3/X509_cmp_time/'}
def digest(o):return hashlib.sha256(json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def experiment(case='wrong-san',mode='offline'):
    if case not in CASES or mode!='offline':raise ValueError('unsupported case/mode; offline fixed fixtures only')
    version=command(['version'])
    from tool import VERSION
    if version['stdout'].strip()!=VERSION:raise RuntimeError('OpenSSL tool version unsupported; no model fallback')
    leaf,ca,epoch=CASES[case];cert='certs/leaf-'+leaf+'.pem';trust='certs/root-'+ca+'.pem'
    inputs={'case':case,'certificate':cert,'trustAnchor':trust,'expectedHostname':'api.atlas.invalid','purpose':'sslserver','verificationEpoch':epoch,'defaultTrustDisabled':True}
    fields=command(['x509','-in',cert,'-noout','-subject','-issuer','-serial','-dates','-ext','subjectAltName,extendedKeyUsage,basicConstraints,keyUsage'])
    base=['verify','-no-CAfile','-no-CApath','-no-CAstore','-CAfile',trust,'-attime',str(epoch),'-x509_strict','-check_ss_sig']
    runs={'strict':command([*base,'-purpose','sslserver','-verify_hostname','api.atlas.invalid',cert]),'noName':command([*base,'-purpose','sslserver',cert]),'chainOnly':command([*base,cert])}
    for row in runs.values():row['accepted']=row['exit']==0
    raw={'fields':fields,'runs':runs};return {'input':inputs,'inputSha256':digest(inputs),'raw':raw,'rawSha256':digest(raw),'version':version['stdout'].strip(),'tlsConnected':False,'osTrustChanged':False}
