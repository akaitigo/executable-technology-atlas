"""Synthetic nine-bit DAC subset. No access/chmod/stat of real targets."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCES={'permissions':'https://man7.org/linux/man-pages/man7/path_resolution.7.html','mode':'https://man7.org/linux/man-pages/man7/inode.7.html','privilege':'https://man7.org/linux/man-pages/man7/capabilities.7.html'}
def canonical(o):return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def digest(o):return hashlib.sha256(canonical(o).encode()).hexdigest()
def validate(mode,inode,actor,operation,kind,security):
    if security!='none':raise ValueError('unsupported security profile: root/ACL/capabilities/LSM/fsuid override outside subset')
    if type(mode)is not str or not re.fullmatch('[0-7]{3}',mode):raise ValueError('mode must be exactly three octal digits 000..777; special bits unsupported')
    if type(inode)is not dict or set(inode)!={'ownerUid','ownerGid'}:raise ValueError('inode schema')
    if type(actor)is not dict or set(actor)!={'uid','gid','supplementary'}:raise ValueError('actor schema')
    ids=[inode['ownerUid'],inode['ownerGid'],actor['uid'],actor['gid']]
    if any(type(v)is not int or not 0<=v<=65535 for v in ids):raise ValueError('ID integer bound 0..65535')
    if actor['uid']==0:raise ValueError('root uid0 unsupported; no bypass modeled')
    if type(actor['supplementary'])is not list or len(actor['supplementary'])>3 or any(type(v)is not int or not 0<=v<=65535 for v in actor['supplementary']):raise ValueError('supplementary group bound 0..3 IDs')
    if kind not in ('file','directory'):raise ValueError('unsupported inode kind')
    if operation not in ('read','write','execute','search','read-write'):raise ValueError('unsupported operation')
    if operation=='execute' and kind!='file' or operation=='search' and kind!='directory':raise ValueError('execute is file; search is directory in subset')

def decide(mode,inode,actor,operation='read',kind='file',security='none'):
    raw={'mode':mode,'inode':inode,'actor':actor,'operation':operation,'kind':kind,'security':security};trace=[]
    try:
        validate(mode,inode,actor,operation,kind,security);number=int(mode,8)
        triplets={'owner':(number>>6)&7,'group':(number>>3)&7,'other':number&7}
        owner=actor['uid']==inode['ownerUid'];primary=actor['gid']==inode['ownerGid'];supplementary=inode['ownerGid'] in actor['supplementary']
        selected='owner' if owner else 'group' if primary or supplementary else 'other'
        reason='uid matches owner' if owner else 'primary gid matches' if primary else 'supplementary gid matches' if supplementary else 'no owner/group match'
        trace.append({'phase':'decode-mode','octal':mode,'decimal':number,'nineBits':format(number,'09b'),'triplets':triplets})
        trace.append({'phase':'select-once','ownerMatch':owner,'primaryMatch':primary,'supplementaryMatch':supplementary,'selected':selected,'reason':reason,'fallback':False})
        request={'read':4,'write':2,'execute':1,'search':1,'read-write':6}[operation];bits=triplets[selected];intersection=bits&request;allow=intersection==request
        trace.append({'phase':'check-selected','selectedBits':bits,'requestMask':request,'intersection':intersection,'allowed':allow})
        protected={'status':'decided','selected':selected,'selectedBits':bits,'requestMask':request,'allowed':allow,'fallback':False,'trace':trace,'error':None}
        union=triplets['owner']|triplets['group']|triplets['other'];bad={'mode':'intentional any-class union','unionBits':union,'requestMask':request,'allowed':(union&request)==request,'trace':[{'phase':'union-all-classes','triplets':triplets,'union':union}]}
    except ValueError as e:
        protected={'status':'rejected','selected':None,'selectedBits':None,'requestMask':None,'allowed':None,'fallback':False,'trace':trace,'error':str(e)}
        bad={'mode':'not-run for unsupported input','unionBits':None,'requestMask':None,'allowed':None,'trace':[]}
    return {'input':raw,'inputSha256':digest(raw),'protected':protected,'bad':bad,'traceSha256':digest({'protected':protected['trace'],'bad':bad['trace']}),'kernelObserved':False,'filesChanged':False}

def experiment(mode='004',principal='owner',operation='read',kind='file',security='none'):
    f=json.loads((ROOT/'fixtures.json').read_text())
    if principal not in f['principals']:raise ValueError('unsupported principal fixture')
    d=decide(mode,f['inode'],f['principals'][principal],operation,kind,security);d['principal']=principal;return d
