'use strict';
// Atlas: wrapper arguments enter actual Wasm exports, which call preview1 imports.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),os=require('node:os');
const ROOT=__dirname,sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const ids=['granted','directory-before-open','file-read-reduced','opened-before-directory-change'];
const record={title:'Atlas actual WASI read and inheriting observations',schema:1,started_at_utc:new Date().toISOString(),runtime:{node:process.versions.node,uvwasi:process.versions.uvwasi,wasi:'preview1'},status:'preparing',cases:[],host_fixture_read:false,fixture_written_by_parent:true,later_cases_not_started:ids.slice()};
const emit=(kind,value)=>console.log(JSON.stringify({kind,...value}));
const need=(ok,text)=>{if(!ok)throw Error(text);};
function runCase(caseId,module,fixture,WASI){
 const r={case_id:caseId,stage:'preparation',events:[],rights:{directory_before:null,directory_after:null,file_before:null,file_after:null},outcome:null,error:null,cleanup:{preopen_created:false,guest_initialized:false,file_closes:[],preopen_close_errno:null,complete:false}};
 let guest=null,view=null,ownedPreopen=false;const ownedFiles=new Set();
 function call(exportName,op,args,role,phase){
  const e=guest[exportName](...args),event={sequence:r.events.length,op,wrapper_args:args.map(v=>typeof v==='bigint'?String(v):v),role,phase,errno:e,output:null};r.events.push(event);return event;
 }
 function publish(e,output=null){e.output=output;emit('event',{case_id:caseId,event:e});return e;}
 function stat(fd,role,phase){new Uint8Array(guest.memory.buffer).fill(0xaa,256,280);const e=call('fdstat','fd_fdstat_get',[fd],role,phase);if(e.errno!==0){publish(e,{rights:null,output_used:false});throw Error('fdstat failed');}const value={base:String(view.getBigUint64(264,true)),inheriting:String(view.getBigUint64(272,true))};publish(e,{...value,output_used:true});return value;}
 function decrease(fd,role,before,which){
  const base=BigInt(before.base)&(which==='base'?~2n:-1n),inheriting=BigInt(before.inheriting)&(which==='inheriting'?~2n:-1n);
  need(((BigInt(before[which])&2n)!==0n),'FD_READ not present before decrease');
  const e=publish(call('reduce','fd_fdstat_set_rights',[fd,base,inheriting],role,'decrease'));need(e.errno===0,'decrease failed');return stat(fd,role,'after');
 }
 function open(phase){
  view.setUint32(320,0xffffffff,true);const e=call('open','path_open',[3,128,8],'directory',phase);
  if(e.errno!==0){publish(e,{opened_fd:null,output_used:false});return {errno:e.errno,fd:null};}
  const fd=view.getUint32(320,true);need(Number.isInteger(fd)&&fd>3&&fd<0xffffffff,'invalid returned FD');ownedFiles.add(fd);publish(e,{opened_fd:fd,output_used:true});return {errno:0,fd};
 }
 function read(fd,expectedRefusal){
  const chunks=[];let eof=false;
  for(let i=0;i<8;i++){
   view.setUint32(392,0xffffffff,true);new Uint8Array(guest.memory.buffer).fill(0xaa,512,520);
   const e=call('read','fd_read',[fd],'file','read');
   if(e.errno!==0){publish(e,{nread:null,hex:null,output_used:false});need(expectedRefusal&&e.errno===76,'unexpected read refusal');return {read_status:'rights_refusal',read_errno:76,hex:null,nread_total:null};}
   const n=view.getUint32(392,true);need(n<=8,'read bound');const b=Buffer.from(new Uint8Array(guest.memory.buffer,512,n));publish(e,{nread:n,hex:b.toString('hex'),output_used:true});need(!expectedRefusal,'read unexpectedly permitted');chunks.push(b);if(n===0){eof=true;break;}
  }
  need(eof,'EOF not observed within bounded reads');const all=Buffer.concat(chunks);need(all.toString('hex')==='41746c61730a','fixture bytes mismatch');return {read_status:'success_then_eof',read_errno:0,hex:all.toString('hex'),nread_total:all.length};
 }
 try{
  const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{'/lesson':fixture},returnOnExit:true});ownedPreopen=true;r.cleanup.preopen_created=true;
  const instance=new WebAssembly.Instance(module,wasi.getImportObject());wasi.initialize(instance);guest=instance.exports;view=new DataView(guest.memory.buffer);r.cleanup.guest_initialized=true;r.stage='WASI';
  new Uint8Array(guest.memory.buffer).fill(0xaa,0,8);const p=call('prestat','fd_prestat_get',[3],'directory','discover');if(p.errno!==0){publish(p,{name_length:null,output_used:false});throw Error('expected preopen unavailable');}const len=view.getUint32(4,true);publish(p,{name_length:len,output_used:true});need(len<=32,'guest name bound');
  const pn=call('prestat_name','fd_prestat_dir_name',[3,len],'directory','discover');if(pn.errno!==0){publish(pn,{guest_name:null,output_used:false});throw Error('guest name failed');}const name=Buffer.from(guest.memory.buffer,64,len).toString('utf8');publish(pn,{guest_name:name,output_used:true});need(name==='/lesson','wrong guest preopen');
  r.rights.directory_before=stat(3,'directory','before');r.rights.directory_after=r.rights.directory_before;need((BigInt(r.rights.directory_before.base)&8192n)!==0n&&(BigInt(r.rights.directory_before.inheriting)&2n)!==0n,'required initial directory rights absent');
  const out={guest_name:name,open_errnos:[],read_status:'not_reached',read_errno:null,hex:null,nread_total:null,classification:null};r.outcome=out;
  if(caseId==='directory-before-open')r.rights.directory_after=decrease(3,'directory',r.rights.directory_before,'inheriting');
  const first=open('first_open');out.open_errnos.push(first.errno);
  if(caseId==='directory-before-open'){need(first.errno===76,'new open unexpectedly permitted');out.classification='new_open_refused';}
  else{
   need(first.errno===0,'first open failed');r.rights.file_before=stat(first.fd,'file','before');need(r.rights.file_before.base==='2'&&r.rights.file_before.inheriting==='0','returned file rights differ');
   if(caseId==='file-read-reduced')r.rights.file_after=decrease(first.fd,'file',r.rights.file_before,'base');
   else if(caseId==='opened-before-directory-change'){r.rights.directory_after=decrease(3,'directory',r.rights.directory_before,'inheriting');r.rights.file_after=stat(first.fd,'file','after');}
   Object.assign(out,read(first.fd,caseId==='file-read-reduced'));
   if(caseId==='granted')r.rights.file_after=stat(first.fd,'file','after');
   if(caseId==='opened-before-directory-change'){const second=open('new_open_after_change');out.open_errnos.push(second.errno);need(second.errno===76,'new open unexpectedly permitted');}
   out.classification=caseId==='file-read-reduced'?'file_read_refused':caseId==='opened-before-directory-change'?'old_read_allowed_new_open_refused':'read_allowed';
  }
  r.stage='observed';
 }catch(e){r.error={name:e.name,message:String(e.message),stack:String(e.stack)};r.stage=guest?'execution_failed':'preparation_failed';}
 finally{
  if(guest){for(const fd of [...ownedFiles]){try{const e=publish(call('close','fd_close',[fd],'file','cleanup'));r.cleanup.file_closes.push({fd,errno:e.errno});if(e.errno===0)ownedFiles.delete(fd);}catch(e){r.cleanup.file_closes.push({fd,error:String(e)});}}if(ownedPreopen){try{const e=publish(call('close','fd_close',[3],'directory','cleanup'));r.cleanup.preopen_close_errno=e.errno;if(e.errno===0)ownedPreopen=false;}catch(e){r.cleanup.preopen_close_error=String(e);}}}
  r.cleanup.complete=ownedFiles.size===0&&!ownedPreopen;r.cleanup.remaining_file_fds=[...ownedFiles];r.cleanup.guest_preopen_close_unconfirmed=ownedPreopen;r.cleanup.recovery=r.cleanup.complete?'explicit guest close complete':'guest close unconfirmed; parent must observe child exit for OS recovery';if(!r.cleanup.complete)r.stage='cleanup_failed';
  emit('case',{case:r});
 }
 return r;
}
async function main(){try{
 need(process.argv.length===3,'one owned fixture argument required');const fixture=path.resolve(process.argv[2]),parent=path.dirname(fixture);need(path.dirname(parent)===path.join(ROOT,'observations')&&/^runtime-\d+T\d+Z$/.test(path.basename(parent))&&path.basename(fixture)==='fixture','fixture must be owned by this run');need(fs.realpathSync(fixture)===fixture&&!fs.lstatSync(fixture).isSymbolicLink()&&!fs.lstatSync(path.join(fixture,'note.txt')).isSymbolicLink(),'owned non-symlink fixture required');
 need(process.versions.node==='25.2.1'&&process.versions.uvwasi==='0.0.23','unexpected fixed runtime');record.priority_observed=os.getPriority(0);need(record.priority_observed===10,'actual nice10 required');
 const bytes=fs.readFileSync(path.join(ROOT,'module.wasm'));record.module_sha256=sha(bytes);need(record.module_sha256==='41e5f0061be53f32aa28eb769a0527d91477a16d9e2e44fb5fbe2ada7916fadf','module changed');record.fixture_sha256=sha(fs.readFileSync(path.join(ROOT,'fixtures.json')));
 const module=await WebAssembly.compile(bytes);const {WASI}=require('node:wasi');record.status='running';
 for(const id of ids){const c=runCase(id,module,fixture,WASI);record.cases.push(c);record.later_cases_not_started=ids.slice(record.cases.length);need(c.stage==='observed'&&c.cleanup.complete,'case failed; no next instance');}
 record.status='observed';
 }catch(e){record.status=record.cases.length?'execution_failed':'preparation_failed';record.error={name:e.name,message:String(e.message),stack:String(e.stack)};process.exitCode=3;}
 finally{record.finished_at_utc=new Date().toISOString();emit('result',{result:record});}
}
main();
