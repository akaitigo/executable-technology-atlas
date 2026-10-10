'use strict';
// Atlas: deliberately small hand-encoded guest. Does not read the independent contract.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const u=n=>{const b=[];do{let x=n&127;n=Math.floor(n/128);b.push(x|(n?128:0));}while(n);return b;};
const s=n=>{const b=[];let more=true;while(more){let x=n&127;n>>=7;more=!((n===0&&!(x&64))||(n===-1&&(x&64)));b.push(x|(more?128:0));}return b;};
const str=t=>[...u(Buffer.byteLength(t)),...Buffer.from(t)];
const vec=a=>[...u(a.length),...a.flat()];
const section=(id,b)=>[id,...u(b.length),...b];
const I=0x7f,L=0x7e;
const types=[[I,I],[I,I,I],[I,I],[I,L,L],[I,I,I,I,I,L,L,I,I],[I,I,I,I],[I], [I],[I,I],[I],[I,L,L],[I,I,I],[I],[I]];
const names=['fd_prestat_get','fd_prestat_dir_name','fd_fdstat_get','fd_fdstat_set_rights','path_open','fd_read','fd_close'];
const exportNames=['prestat','prestat_name','fdstat','reduce','open','read','close'];
const get=n=>[0x20,...u(n)],i=n=>[0x41,...s(n)],l=n=>[0x42,...s(n)],call=n=>[0x10,...u(n)];
const bodies=[
 [...get(0),...i(0),...call(0)],
 [...get(0),...i(64),...get(1),...call(1)],
 [...get(0),...i(256),...call(2)],
 [...get(0),...get(1),...get(2),...call(3)],
 [...get(0),...i(0),...get(1),...get(2),...i(0),...l(2),...l(0),...i(0),...i(320),...call(4)],
 [...get(0),...i(384),...i(1),...i(392),...call(5)],
 [...get(0),...call(6)]];
const data=[[128,Buffer.from('note.txt')],[160,Buffer.from('absent.txt')],[384,Buffer.from('0002000008000000','hex')]];
const bytes=Buffer.from([0,97,115,109,1,0,0,0,
 ...section(1,vec(types.map(a=>[0x60,...vec(a.map(x=>[x])),1,I]))),
 ...section(2,vec(names.map((n,k)=>[...str('wasi_snapshot_preview1'),...str(n),0,...u(k)]))),
 ...section(3,vec(exportNames.map((_,k)=>u(k+7)))),
 ...section(5,[1,1,1,1]),
 ...section(7,vec([[...str('memory'),2,0],...exportNames.map((n,k)=>[...str(n),0,...u(k+7)])])),
 ...section(10,vec(bodies.map(b=>{const body=[0,...b,0x0b];return [...u(body.length),...body];}))),
 ...section(11,vec(data.map(([offset,b])=>[0,...i(offset),0x0b,...u(b.length),...b])))
]);
const out=path.join(__dirname,'module.wasm');if(fs.existsSync(out))throw Error('Atlas: module.wasm already exists; preserve it before changing.');
fs.writeFileSync(out,bytes);console.log(JSON.stringify({bytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex'),wasm_executed:false}));
