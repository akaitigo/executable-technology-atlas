import test from 'node:test';
import assert from 'node:assert/strict';
const schedule=process.env.ATLAS_SCHEDULE,variant=process.env.ATLAS_VARIANT;
let sequence=0;
function emit(event,fields={}){console.log('ATLAS_EVENT '+JSON.stringify({event,seq:sequence++,pid:process.pid,...fields}));}
if(!['assert-before-update','update-before-assert'].includes(schedule)||!['unawaited','await-completion'].includes(variant)){
 emit('input_refused',{reason:'unsupported schedule or variant'});process.exit(2);
}
function gate(){let release;const promise=new Promise(resolve=>{release=resolve});return {promise,release};}
let value=0,released=false;
const updateGate=gate(),testEntered=gate();
function releaseUpdate(){if(!released){released=true;emit('gate_released');updateGate.release();}}
const work=(async()=>{emit('update_waiting',{value});await updateGate.promise;value=1;emit('value_updated',{value});})();
work.then(()=>emit('work_settled',{value}));
function assertBody(){
 emit('assert_read',{value,expected:1});
 try{assert.strictEqual(value,1);emit('assert_passed',{value});}
 catch(error){emit('assert_failed',{value,code:error.code,actual:error.actual,expected:error.expected});throw error;}
}
try{
 if(schedule==='update-before-assert'){releaseUpdate();await work;}
 const done=test('same assertion body',async()=>{
  emit('test_entered',{value});testEntered.release();
  if(variant==='await-completion'){emit('completion_await_started');await work;emit('completion_await_finished',{value});}
  assertBody();
 });
 if(schedule==='assert-before-update'){
  await testEntered.promise;
  if(variant==='unawaited')await done;
  releaseUpdate();
 }
 await done;
}finally{
 releaseUpdate();await work;emit('cleanup_complete',{value,work_settled:true,gate_released:released});
}
