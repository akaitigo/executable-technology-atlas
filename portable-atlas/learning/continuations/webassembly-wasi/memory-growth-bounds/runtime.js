// SPDX-License-Identifier: Apache-2.0
import {moduleBytes} from './binary.js';
export async function runCase(id,address){
 const r={case:id,address,started_utc:new Date().toISOString(),status:null,stage:'host-validation',instantiated:false,events:[],module_hex:null,module_sha256:null};
 const finish=()=>{r.ended_utc=new Date().toISOString();return r};
 const event=(op,fn,extra={})=>{try{let value=fn();r.events.push({op,...extra,outcome:'value',kind:typeof value,value:value===undefined?null:value});return value}catch(e){r.events.push({op,...extra,outcome:'exception',error_class:e.constructor.name,error_message:e.message});return null}};
 if(typeof address!=='number'||!Number.isInteger(address)||address<0||address>131072){r.status='REFUSED_INPUT';r.error='address number/integer 0..131072 required';return finish()}
 if(!['last-byte','initial-oob','grow-one','js-max','core-max','execution-failure'].includes(id)){r.status='REFUSED_INPUT';r.error='case refused';return finish()}
 try{
  r.stage='executor';if(id==='execution-failure')throw new Error('injected host executor unavailable');
  const bytes=moduleBytes();r.module_hex=Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');r.module_sha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
  r.stage='instantiate';const {instance}=await WebAssembly.instantiate(bytes);r.instantiated=true;r.stage='invoke';
  const mem=instance.exports.memory,oldBuffer=mem.buffer,oldTyped=new Uint8Array(oldBuffer),oldData=new DataView(oldBuffer);
  event('initial-bytes',()=>oldBuffer.byteLength);event('initial-shared',()=>typeof SharedArrayBuffer!=='undefined'&&oldBuffer instanceof SharedArrayBuffer);event('initial-resizable',()=>oldBuffer.resizable===true);
  oldTyped[0]=7;oldTyped[65535]=171;r.events.push({op:'host-writes',writes:[[0,7],[65535,171]]});
  const load=a=>event('core-load8',()=>instance.exports.load8(a),{address:a});
  if(id==='last-byte'||id==='initial-oob'){load(address);r.status=r.events.at(-1).outcome==='exception'?'EXPECTED_TRAP':'LOAD_OK'}
  else if(id==='grow-one'){
   event('js-grow',()=>mem.grow(1),{delta:1});if(r.events.at(-1).outcome==='exception'){r.status='EXECUTION_FAILURE';r.error='grow-one did not complete';return finish()}event('new-bytes',()=>mem.buffer.byteLength);event('buffer-replaced',()=>mem.buffer!==oldBuffer);
   event('old-buffer-bytes',()=>oldBuffer.byteLength);event('old-typed-length',()=>oldTyped.length);event('old-typed-index',()=>oldTyped[0]);event('old-typed-slice',()=>oldTyped.slice(0,1));event('old-data-byteLength',()=>oldData.byteLength);event('old-data-get',()=>oldData.getUint8(0));
   const fresh=new Uint8Array(mem.buffer);event('new-typed-length',()=>fresh.length);event('new-data-get',()=>new DataView(mem.buffer).getUint8(0));
   for(const a of [0,65535,65536,131071,131072])load(a);
   r.status='GROWN';
  }else{
   if(id==='js-max'){event('js-grow',()=>mem.grow(2),{delta:2});r.status='EXPECTED_JS_GROW_FAILURE'}
   else{event('core-grow',()=>instance.exports.grow(2),{delta:2});r.status='EXPECTED_CORE_GROW_FAILURE'}
   event('after-bytes',()=>mem.buffer.byteLength);event('buffer-same',()=>mem.buffer===oldBuffer);event('old-typed-length',()=>oldTyped.length);event('old-data-get',()=>oldData.getUint8(0));load(65535);
  }
  r.stage='complete';return finish();
 }catch(e){r.status='EXECUTION_FAILURE';r.error_class=e.constructor.name;r.error_message=e.message;return finish()}
}
