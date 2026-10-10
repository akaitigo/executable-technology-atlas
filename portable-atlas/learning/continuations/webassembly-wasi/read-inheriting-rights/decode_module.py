"""Atlas: independently decode the small binary; never invoke WebAssembly."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
T={0x7f:'i32',0x7e:'i64'}

class Reader:
    def __init__(self,data): self.data=data;self.at=0
    def take(self,n):
        if n<0 or self.at+n>len(self.data): raise ValueError('truncated binary')
        b=self.data[self.at:self.at+n];self.at+=n;return b
    def byte(self): return self.take(1)[0]
    def leb(self,signed=False):
        n=0;shift=0
        for _ in range(10):
            b=self.byte();n|=(b&127)<<shift;shift+=7
            if b<128:
                if signed and b&64:n-=1<<shift
                return n
        raise ValueError('unbounded LEB')
    def text(self): return self.take(self.leb()).decode('utf-8')
    def done(self):
        if self.at!=len(self.data):raise ValueError('unconsumed bytes')
    def vector(self,fn):return [fn() for _ in range(self.leb())]

def decode(data):
    r=Reader(data)
    if r.take(8)!=b'\0asm\1\0\0\0':raise ValueError('magic/version')
    sec={};ids=[]
    while r.at<len(data):
        n=r.byte();ids.append(n);sec[n]=Reader(r.take(r.leb()))
    if ids!=[1,2,3,5,7,10,11]:raise ValueError('unexpected sections')
    a=sec[1]
    def typ():
        if a.byte()!=0x60:raise ValueError('function type')
        return {'params':a.vector(lambda:T[a.byte()]),'results':a.vector(lambda:T[a.byte()])}
    types=a.vector(typ);a.done()
    a=sec[2]
    def imp():
        module=a.text();name=a.text()
        if a.byte()!=0:raise ValueError('nonfunction import')
        return {'module':module,'name':name,'type':a.leb()}
    imports=a.vector(imp);a.done()
    a=sec[3];indices=a.vector(a.leb);a.done()
    a=sec[5]
    if a.leb()!=1 or a.byte()!=1:raise ValueError('bounded single memory required')
    memory={'minimum_pages':a.leb(),'maximum_pages':a.leb(),'export':'memory'};a.done()
    a=sec[7];exports=a.vector(lambda:{'name':a.text(),'kind':a.byte(),'index':a.leb()});a.done()
    if len({x['name'] for x in exports})!=len(exports):raise ValueError('duplicate export')
    a=sec[10];functions=[];all_types=[x['type'] for x in imports]+indices
    count=a.leb()
    if count!=len(indices):raise ValueError('function/code count')
    for k in range(count):
        b=Reader(a.take(a.leb()))
        if b.leb()!=0:raise ValueError('locals outside fixed subset')
        signature=types[indices[k]];stack=[];ops=[]
        while b.at<len(b.data):
            opcode=b.byte()
            if opcode==0x0b:
                ops.append(['end']);b.done();break
            if opcode==0x20:
                ix=b.leb();stack.append(signature['params'][ix]);ops.append(['local.get',ix])
            elif opcode in [0x41,0x42]:
                n=b.leb(True);kind='i32' if opcode==0x41 else 'i64';stack.append(kind);ops.append([kind+'.const',n])
            elif opcode==0x10:
                ix=b.leb();callee=types[all_types[ix]]
                for expected in reversed(callee['params']):
                    if not stack or stack.pop()!=expected:raise ValueError('call stack type mismatch')
                stack.extend(callee['results']);ops.append(['call',ix])
            else:raise ValueError('opcode outside audited subset')
        if not ops or ops[-1]!=['end'] or stack!=signature['results']:raise ValueError('result stack mismatch')
        candidates=[x['name'] for x in exports if x['kind']==0 and x['index']==k+len(imports)]
        if len(candidates)!=1:raise ValueError('function export missing')
        functions.append(dict(name=candidates[0],**signature,code=ops))
    a.done();a=sec[11];segments=[]
    for _ in range(a.leb()):
        if a.leb()!=0 or a.byte()!=0x41:raise ValueError('data mode')
        offset=a.leb(True)
        if a.byte()!=0x0b:raise ValueError('data offset end')
        content=a.take(a.leb())
        if offset<0 or offset+len(content)>memory['minimum_pages']*65536:raise ValueError('data bounds')
        segments.append({'offset':offset,'hex':content.hex()})
    a.done()
    return {'imports':[dict(module=x['module'],name=x['name'],**types[x['type']]) for x in imports], 'functions':functions,'memory':memory,'data':segments,'exports':exports,'sections':ids}

def verify_binary(data,contract=None):
    c=contract or json.loads((ROOT/'module-contract.json').read_text());d=decode(data)
    expected=[dict(module=c['import_module'],**x) for x in c['imports']]
    if d['imports']!=expected:raise ValueError('import contract mismatch')
    for key in ['functions','memory','data']:
        if d[key]!=c[key]:raise ValueError(key+' contract mismatch')
    if d['exports']!=[{'name':'memory','kind':2,'index':0}]+[{'name':x['name'],'kind':0,'index':7+i} for i,x in enumerate(c['functions'])]:raise ValueError('export contract mismatch')
    return d

if __name__=='__main__':
    print(json.dumps({'Atlas':'independent binary decoding','decoded':verify_binary((ROOT/'module.wasm').read_bytes()),'wasm_executed':False},ensure_ascii=False,indent=2))
