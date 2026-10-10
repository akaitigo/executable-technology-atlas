'use strict';
// Atlas: host prepares bindings, guest exports execute the real WASI imports.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=__dirname,sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const [caseId,fixtureArg]=process.argv.slice(2);
const allowed=new Set(['no-preopen','granted','rights-reduced','missing-file']);
if(process.argv.length!==4||!allowed.has(caseId)||!fixtureArg){console.error('Atlas REFUSED_INPUT: fixed case and owned fixture required');process.exit(2);}
const fixture=path.resolve(fixtureArg),ownedRoot=path.join(root,'observations');
if(!fixture.startsWith(ownedRoot+path.sep)||path.basename(fixture)!=='fixture'||fs.lstatSync(fixture).isSymbolicLink()||fs.realpathSync(fixture)!==fixture){console.error('Atlas REFUSED_INPUT: fixture outside own observations');process.exit(2);}
if(process.versions.node!=='25.2.1'||process.versions.uvwasi!=='0.0.23'){console.error('Atlas PREPARATION_FAILED: unexpected runtime');process.exit(3);}
const r={title:'Atlas 実WASI呼出しの保存記録',case_id:caseId,started_at_utc:new Date().toISOString(),runtime:{node:process.versions.node,uvwasi:process.versions.uvwasi,v8:process.versions.v8,wasi:'preview1'},events:[],outcome:null,stage:'preparation',error:null,cleanup:{file_close_errno:null,preopen_close_errno:null,complete:false},host_fixture_read:false};
let guest=null,ownedPreopen=false,openedFd=null,view=null;
const note=(op,args,errno,output=null)=>{r.events.push({sequence:r.events.length,op,args:args.map(v=>typeof v==='bigint'?String(v):v),errno,output});return errno;};
function invoke(name,args,op){const e=guest[name](...args);note(op||name,args,e);return e;}
function lastOutput(value){r.events.at(-1).output=value;}
function fdstat(){const e=invoke('fdstat',[3],'fd_fdstat_get');if(e!==0)throw Error('fdstat failed: '+e);const value={base:String(view.getBigUint64(264,true)),inheriting:String(view.getBigUint64(272,true))};lastOutput(value);return value;}
async function main(){try{
 const {WASI}=require('node:wasi');
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:caseId==='no-preopen'?{}:{'/lesson':fixture},returnOnExit:true});
 ownedPreopen=caseId!=='no-preopen';
 const bytes=fs.readFileSync(path.join(root,'module.wasm'));r.module_sha256=sha(bytes);
 const module=await WebAssembly.compile(bytes);r.stage='instantiation';
 const instance=await WebAssembly.instantiate(module,wasi.getImportObject());wasi.initialize(instance);guest=instance.exports;view=new DataView(guest.memory.buffer);r.stage='WASI';
 const out={prestat_errno:null,guest_name:null,reduce_errno:null,path_open_errno:null,read_status:'not_reached',hex:null,nread_total:null,classification:null};
 out.prestat_errno=invoke('prestat',[3],'fd_prestat_get');
 if(out.prestat_errno!==0){out.classification='descriptor_unavailable';r.outcome=out;r.stage='observed';return;}
 ownedPreopen=true;const nameLength=view.getUint32(4,true);if(nameLength>32)throw Error('prestat name bound');lastOutput({directory_name_length:nameLength});
 const ne=invoke('prestat_name',[3,nameLength],'fd_prestat_dir_name');if(ne!==0)throw Error('prestat name failed');out.guest_name=Buffer.from(guest.memory.buffer,64,nameLength).toString('utf8');lastOutput({guest_name:out.guest_name});
 r.rights_before=fdstat();r.rights_after=r.rights_before;
 if(caseId==='rights-reduced'){
  const base=BigInt(r.rights_before.base)&~8192n,inherit=BigInt(r.rights_before.inheriting);
  out.reduce_errno=invoke('reduce',[3,base,inherit],'fd_fdstat_set_rights');if(out.reduce_errno!==0)throw Error('rights decrease failed');r.rights_after=fdstat();
 }
 const missing=caseId==='missing-file';view.setUint32(320,0xffffffff,true);
 out.path_open_errno=invoke('open',[3,missing?160:128,missing?10:8],'path_open');
 if(out.path_open_errno!==0){lastOutput({opened_fd:null,output_used:false});out.classification=out.path_open_errno===76?'rights_refusal':out.path_open_errno===44?'missing_entry':'unexpected_errno';r.outcome=out;r.stage='observed';return;}
 openedFd=view.getUint32(320,true);if(openedFd===0xffffffff||openedFd===3||openedFd<3)throw Error('invalid returned file FD');lastOutput({opened_fd:openedFd,output_used:true});
 const chunks=[];let eof=false;
 for(let k=0;k<8;k++){
  view.setUint32(392,0xffffffff,true);const e=invoke('read',[openedFd],'fd_read');
  if(e!==0){lastOutput({nread:null,bytes:null,output_used:false});throw Error('fd_read failed: '+e);}
  const n=view.getUint32(392,true);if(n>8)throw Error('read bound');const b=Buffer.from(guest.memory.buffer,512,n);lastOutput({nread:n,hex:b.toString('hex'),output_used:true});chunks.push(Buffer.from(b));if(n===0){eof=true;break;}
 }
 if(!eof)throw Error('read call bound exceeded without EOF');
 const bytesRead=Buffer.concat(chunks);out.read_status='success_then_eof';out.hex=bytesRead.toString('hex');out.nread_total=bytesRead.length;out.classification='bytes_observed';r.outcome=out;r.stage='observed';
}catch(e){r.error={name:e.name,message:String(e.message),stack:String(e.stack)};r.stage=r.stage==='preparation'?'preparation_failed':'execution_failed';process.exitCode=3;}
finally{
 if(guest&&openedFd!==null){try{r.cleanup.file_close_errno=invoke('close',[openedFd],'fd_close_file');if(r.cleanup.file_close_errno===0)openedFd=null;}catch(e){r.cleanup.file_close_error=String(e);}}
 if(guest&&ownedPreopen){try{r.cleanup.preopen_close_errno=invoke('close',[3],'fd_close_preopen');if(r.cleanup.preopen_close_errno===0)ownedPreopen=false;}catch(e){r.cleanup.preopen_close_error=String(e);}}
 r.cleanup.complete=openedFd===null&&!ownedPreopen;
 if(!r.cleanup.complete){r.stage='cleanup_failed';process.exitCode=4;}
 r.finished_at_utc=new Date().toISOString();console.log(JSON.stringify(r));
}}
main();
