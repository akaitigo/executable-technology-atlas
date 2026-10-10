// Producer performs real Worker/ArrayBuffer operations; does not read oracle.
export async function run(caseName,fixture,sourceBinding){
  const session=crypto.randomUUID(),dataID=session+':data',acks=[],actions=[];
  const worker=new Worker('/worker.js'),pending=new Map();
  let phase='start',result;
  const record=(event,detail={})=>actions.push({event,utc:new Date().toISOString(),...detail});
  worker.onmessage=e=>{acks.push(e.data);record('worker-message',{id:e.data.id,kind:e.data.kind});const p=pending.get(e.data.id);if(p){clearTimeout(p.timer);pending.delete(e.data.id);p.resolve(e.data)}};
  worker.onerror=e=>{record('worker-error',{message:e.message});for(const p of pending.values()){clearTimeout(p.timer);p.reject(Error('WorkerError'))}pending.clear()};
  function request(message,transfer=[]){
    return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{pending.delete(message.id);record('timeout',{id:message.id});reject(Error('ACK_TIMEOUT'))},30000);pending.set(message.id,{resolve,reject,timer});record('post-attempt',{id:message.id,kind:message.kind});try{worker.postMessage(message,transfer);record('post-return',{id:message.id})}catch(e){clearTimeout(timer);pending.delete(message.id);record('post-throw',{id:message.id,name:e.name});reject(e)}});
  }
  const before=Uint8Array.from(fixture.bytes).buffer;
  const snapshot=buffer=>{let bytes=null,access_error=null;try{bytes=Array.from(new Uint8Array(buffer))}catch(e){access_error=e.name}return {byte_length:buffer.byteLength,bytes,access_error}};
  try{
    phase='before-probe';const initial=await request({id:session+':before',kind:'probe'});
    const senderBefore=snapshot(before);record('sender-before',senderBefore);
    phase='data-post';const payload={id:dataID,kind:'data',buffer:before,mutate_first_to:fixture.mutate_first_to};if(fixture.contains_function)payload.callback=()=>1;
    // Snapshot synchronously after postMessage returns/throws, then again after ACK.
    let postError=null,dataAck=null;const delivery=request(payload,fixture.transfer?[before]:[]);
    const immediate=snapshot(before);record('sender-immediate',immediate);
    try{dataAck=await delivery}catch(e){if(e.name==='DataCloneError')postError=e.name;else throw e}
    phase='after-probe';const final=await request({id:session+':after',kind:'probe'});
    const senderAfter=snapshot(before);record('sender-after',senderAfter);
    result={status:postError?'EXPECTED_SERIALIZATION_REFUSAL':'DELIVERED',sender_before:senderBefore,sender_immediate:immediate,sender_after_length:senderAfter.byte_length,sender_after_bytes:senderAfter.bytes,sender_access_error:senderAfter.access_error,worker_before_bytes:dataAck?.before??null,worker_after_bytes:dataAck?.after??null,worker_length:dataAck?.byte_length??null,worker_sum:dataAck?.sum??null,post_error:postError,received_data:final.received_data,initial_probe:initial,final_probe:final,data_ack:dataAck};
  }catch(e){result={status:'EXECUTION_FAILURE',phase,error:e.name,message:e.message}}
  finally{worker.terminate();for(const p of pending.values())clearTimeout(p.timer);pending.clear();record('worker-terminated')}
  return {case:caseName,utc:new Date().toISOString(),runtime:{userAgent:navigator.userAgent,platform:navigator.platform,worker:'Dedicated Worker',timeout_ms:30000},fixture,session,data_id:dataID,result,acks,actions,worker_terminated:true,source_binding:sourceBinding};
}
