"""Finite Desktop Entry parser. No process launching API is used."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCES={'format':'https://specifications.freedesktop.org/desktop-entry/latest/basic-format.html','values':'https://specifications.freedesktop.org/desktop-entry/latest/value-types.html','exec':'https://specifications.freedesktop.org/desktop-entry/latest/exec-variables.html','keys':'https://specifications.freedesktop.org/desktop-entry/latest/recognized-keys.html'}
def canonical(o):return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def digest(o):return hashlib.sha256(canonical(o).encode()).hexdigest()
class Rejected(ValueError):
    def __init__(self,kind,message):self.kind=kind;super().__init__(message)
def reject(kind,message):raise Rejected(kind,message)
def parse_entry(text,trace):
    if type(text)is not str or not 0<len(text)<=2048:reject('bound','entry length 1..2048')
    groups={};group=None
    for n,line in enumerate(text.split('\n'),1):
        if not line.strip() or line.startswith('#'):continue
        if line.startswith('['):
            if not re.fullmatch(r'\[[\x20-\x7e]+\]',line) or '[' in line[1:-1] or ']' in line[1:-1]:reject('invalid','group syntax')
            group=line[1:-1]
            if group in groups:reject('invalid','duplicate group')
            if not groups and group!='Desktop Entry':reject('invalid','Desktop Entry must be first group')
            groups[group]={};continue
        if group is None or '=' not in line:reject('invalid','entry outside group or missing equals')
        key,value=line.split('=',1);key=key.strip();value=value.strip()
        if not re.fullmatch('[A-Za-z0-9-]+',key):reject('unsupported','localized/extended key syntax outside subset')
        if key in groups[group]:reject('invalid','duplicate key')
        groups[group][key]=value;trace.append({'phase':'key','line':n,'group':group,'key':key,'rawValue':value})
    entry=groups.get('Desktop Entry',{})
    if any(k not in entry for k in ('Type','Name')) or not entry.get('Name'):reject('invalid','Type and nonempty Name required')
    if entry['Type']!='Application':reject('unsupported','only Application modeled')
    for k in ('Terminal','DBusActivatable'):
        if k in entry and entry[k] not in ('true','false'):reject('invalid','boolean spelling')
        if entry.get(k)=='true':reject('unsupported',k+' launch not modeled')
    if not entry.get('Exec'):reject('invalid','Exec required in this subset')
    behavior={'Path','TryExec','Hidden','NoDisplay','OnlyShowIn','NotShowIn','Actions'}
    if behavior.intersection(entry):reject('unsupported','behavioral key outside subset')
    return groups,entry

def decode_string(raw,trace):
    if any(ord(c)<32 or ord(c)>126 for c in raw):reject('invalid','Exec raw value must be printable ASCII')
    out=[];i=0;esc={'s':' ','n':'\n','t':'\t','r':'\r','\\':'\\'}
    while i<len(raw):
        if raw[i]!='\\':out.append(raw[i]);i+=1;continue
        if i+1>=len(raw) or raw[i+1] not in esc:reject('invalid','string escape')
        out.append(esc[raw[i+1]]);i+=2
    value=''.join(out);trace.append({'phase':'string-unescape','raw':raw,'decoded':value});return value

def tokenize(value,trace):
    tokens=[];i=0;reserved=set("\t\n\r\"'\\><~|&;$*?#()`")
    while i<len(value):
        if value[i]==' ':i+=1;continue
        start=i;quoted=value[i]=='"';chars=[]
        if quoted:
            i+=1;closed=False
            while i<len(value):
                c=value[i]
                if c=='"':i+=1;closed=True;break
                if c=='\\':
                    if i+1>=len(value) or value[i+1] not in ('"','`','$','\\'):reject('invalid','quoted escape')
                    chars.append(value[i+1]);i+=2;continue
                if c in ('$','`'):reject('invalid','reserved quoted character needs escape')
                if c=='\r':reject('unsupported','carriage return outside finite subset')
                chars.append(c);i+=1
            if not closed:reject('invalid','unclosed quote')
            if i<len(value) and value[i]!=' ':reject('invalid','whole argument quoting required')
        else:
            while i<len(value) and value[i]!=' ':
                if value[i] in reserved:reject('invalid','reserved character outside quote')
                chars.append(value[i]);i+=1
        token=''.join(chars);tokens.append({'value':token,'quoted':quoted});trace.append({'phase':'token','start':start,'end':i,'value':token,'quoted':quoted})
    if not tokens or not tokens[0]['value']:reject('invalid','empty executable')
    if '=' in tokens[0]['value']:reject('invalid','equals in executable')
    if tokens[0]['value'] not in ('atlas-viewer','/synthetic/bin/atlas-viewer','/synthetic/My Apps/atlas-viewer'):reject('policy','executable not in teaching allowlist; shell launch forbidden')
    return tokens

def expand(tokens,files,trace):
    filecode=None;count=0;pieces=[]
    for token in tokens:
        value=token['value'];parts=[];i=0
        while i<len(value):
            if value[i]!='%':parts.append(value[i]);i+=1;continue
            if i+1>=len(value):reject('invalid','dangling percent')
            code=value[i+1]
            if token['quoted']:reject('unsupported','field expansion inside quotes undefined; rejected by subset')
            if code=='%':parts.append('%');i+=2;continue
            if code in ('f','F'):
                if value!='%'+code:reject('unsupported','file field must be standalone in subset')
                filecode=code;count+=1;parts=None;i+=2;continue
            if code in 'uUickdDnNvm':reject('unsupported','known field outside subset: %'+code)
            reject('invalid','unknown field: %'+code)
        pieces.append(None if parts is None else ''.join(parts))
    if count>1:reject('invalid','at most one file field')
    selected=[[f] for f in files] if filecode=='f' and files else [files]
    launches=[]
    for selection in selected:
        argv=[]
        for piece in pieces:
            if piece is None:argv.extend(selection)
            else:argv.append(piece)
        launches.append(argv)
    trace.append({'phase':'field-expand-once','field':filecode,'files':files,'argvModels':launches})
    return launches

def compile_entry(text,files,launch='argv-model'):
    trace=[]
    try:
        if launch!='argv-model':reject('policy','only argv-model; no process or shell execution')
        if type(files)is not list or len(files)>3 or any(type(f)is not str or not f.startswith('/synthetic/') or len(f)>128 or any(ord(c)<32 for c in f) for f in files):reject('bound','0..3 synthetic file paths, length <=128')
        groups,entry=parse_entry(text,trace);value=decode_string(entry['Exec'],trace);tokens=tokenize(value,trace);argv=expand(tokens,files,trace)
        result={'status':'modeled','kind':None,'error':None,'groups':groups,'tokens':tokens,'argvModels':argv,'spawned':False,'shell':False,'trace':trace}
    except Rejected as e:result={'status':'rejected','kind':e.kind,'error':str(e),'groups':None,'tokens':None,'argvModels':[],'spawned':False,'shell':False,'trace':trace}
    result['traceSha256']=digest(trace);return result

def experiment(case='quoted',selection='spaces',launch='argv-model'):
    fixture=json.loads((ROOT/'fixtures.json').read_text())
    if case not in fixture['entries'] or selection not in fixture['files']:raise ValueError('unsupported case/selection')
    text=fixture['entries'][case];files=fixture['files'][selection]
    actual=compile_entry(text,files,launch)
    raw_exec=next((line.split('=',1)[1] for line in text.splitlines() if line.startswith('Exec=')),'')
    bad={'mode':'intentional naive split','rawTokens':raw_exec.split(),'argvModel':raw_exec.replace('%F',' '.join(files)).replace('%f',files[0] if files else '').replace('%%','%').split(),'spawned':False,'shell':False}
    return {'input':{'case':case,'selection':selection,'launch':launch,'entry':text,'files':files},'inputSha256':digest({'entry':text,'files':files,'launch':launch}),'protected':actual,'bad':bad}
