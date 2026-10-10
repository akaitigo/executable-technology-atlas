// Actual finite Worker experiment. Setup and constructor are inside failure boundary.
export async function run(caseName,fixture,sourceBinding){
  let session=null,dataID=null,worker=null,phase='setup',result;
  const pending=new Map(),acks=[],actions=[],partial={};
  const record=(event,detail={})=>actions.push({event,utc:new Date().toISOString(),...detail});
  function request(message,transfer=[]){return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{pending.delete(message.id);record('timeout',{id:message.id});reject(Error('ACK_TIMEOUT'))},5000);pending.set(message.id,{resolve,reject,timer});record('post-attempt',{id:message.id,kind:message.kind});try{worker.postMessage(message,transfer);record('post-return',{id:message.id})}catch(e){clearTimeout(timer);pending.delete(message.id);record('post-throw',{id:message.id,name:e.name});reject(e)}})}
  const snapshot=buffer=>{let bytes=null,access_error=null;try{bytes=Array.from(new Uint8Array(buffer))}catch(e){access_error=e.name}return {byte_length:buffer.byteLength,bytes,access_error}};
  try{
    session=crypto.randomUUID();dataID=session+':data';phase='worker-constructor';worker=new Worker('/worker.js');record('worker-created');
    worker.onmessage=e=>{acks.push(e.data);record('worker-message',{id:e.data.id,kind:e.data.kind});const p=pending.get(e.data.id);if(p){clearTimeout(p.timer);pending.delete(e.data.id);p.resolve(e.data)}};
    worker.onerror=e=>{record('worker-error',{message:e.message});for(const p of pending.values()){clearTimeout(p.timer);p.reject(Error('WorkerError'))}pending.clear()};
    phase='buffer-setup';const buffer=Uint8Array.from(fixture.bytes).buffer;
    phase='before-probe';const initial=await request({id:session+':before',kind:'probe'});partial.initial_probe=initial;
    const senderBefore=snapshot(buffer);partial.sender_before=senderBefore;record('sender-before',senderBefore);
    phase='data-post';const payload={id:dataID,kind:'data',buffer,mutate_first_to:fixture.mutate_first_to};if(fixture.contains_function)payload.callback=()=>1;
    let postError=null,dataAck=null;const delivery=request(payload,fixture.transfer?[buffer]:[]);const immediate=snapshot(buffer);partial.sender_immediate=immediate;record('sender-immediate',immediate);
    try{dataAck=await delivery}catch(e){if(e.name==='DataCloneError')postError=e.name;else throw e}
    partial.data_ack=dataAck;phase='after-probe';const final=await request({id:session+':after',kind:'probe'});partial.final_probe=final;
    const senderAfter=snapshot(buffer);record('sender-after',senderAfter);
    result={status:postError?'EXPECTED_SERIALIZATION_REFUSAL':'DELIVERED',sender_before:senderBefore,sender_immediate:immediate,sender_after_length:senderAfter.byte_length,sender_after_bytes:senderAfter.bytes,sender_access_error:senderAfter.access_error,worker_before_bytes:dataAck?.before??null,worker_after_bytes:dataAck?.after??null,worker_length:dataAck?.byte_length??null,worker_sum:dataAck?.sum??null,post_error:postError,received_data:final.received_data,initial_probe:initial,final_probe:final,data_ack:dataAck};
  }catch(e){result={status:'EXECUTION_FAILURE',phase,error:e.name,message:e.message,partial}}
  finally{if(worker){worker.terminate();record('worker-terminated')}else record('worker-not-created');for(const p of pending.values())clearTimeout(p.timer);pending.clear()}
  return {case:caseName,utc:new Date().toISOString(),runtime:{userAgent:navigator.userAgent,platform:navigator.platform,worker:'Dedicated Worker',timeout_ms:5000},fixture,session,data_id:dataID,result,acks,actions,worker_terminated:worker!==null,source_binding:sourceBinding};
}
