import {bytesFor} from './binary.mjs';
export const hex=bytes=>Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');
export const digest=async bytes=>hex(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)));
export async function runCase(c){
  const started=new Date().toISOString(),events=[],mark=(name,detail)=>events.push({name,time:new Date().toISOString(),detail});
  const bytes=bytesFor(c.kind),bytesDigest=await digest(bytes),validated=WebAssembly.validate(bytes);mark('bytes',{length:bytes.length,sha256:bytesDigest});mark('validate',{accepted:validated});
  let stage='instantiate',result=null,error=null,imports=null,exports=null;
  try{
    const linked=await WebAssembly.instantiate(bytes,c.kind==='missing-import'?{env:{}}:{});
    imports=WebAssembly.Module.imports(linked.module);exports=WebAssembly.Module.exports(linked.module);mark('instantiated',{imports,exports});
    stage='invoke';const a=c.kind==='bigint-call'?BigInt(1):c.a;mark('invoke',{export:'add',a:c.kind==='bigint-call'?'1n':a,b:c.b});
    result=linked.instance.exports.add(a,c.b);stage='complete';mark('returned',{result});
  }catch(e){error={name:e.name,message:e.message};mark('rejected',{stage,...error});}
  return {id:c.id,input:c,started,completed:new Date().toISOString(),bytesHex:hex(bytes),bytesDigest,byteLength:bytes.length,validated,stage,imports,exports,result,jsNumberSum:c.kind==='bigint-call'?null:c.a+c.b,error,events};
}
