import assert from 'node:assert/strict';import {readFile,mkdir,writeFile} from 'node:fs/promises';import {createHash} from 'node:crypto';import {initialState,transition,views} from './model.mjs';import {STEPS} from './oracle.mjs';import {SOURCES} from './sources.mjs';
const root=new URL('./',import.meta.url),hash=b=>createHash('sha256').update(b).digest('hex');
const sourceHashes=Object.fromEntries(await Promise.all(SOURCES.map(async f=>[f,hash(await readFile(new URL(f,root)))])));
const startedAt=new Date().toISOString(),observations=[];let state=initialState(),checks=0;
for(const step of STEPS) {
 const before=structuredClone(state),at=new Date().toISOString();
 const result=step.input?transition(state,step.input):{state,outcome:{accepted:true,reason:'initial'}};
 assert.deepEqual(state,before);checks++;
 state=result.state;assert.deepEqual(state,step.state);assert.deepEqual(views(state),step.views);assert.deepEqual(result.outcome,step.outcome);checks+=3;
 observations.push({id:step.id,input:step.input,at,completedAt:new Date().toISOString(),before,state:structuredClone(state),views:views(state),outcome:result.outcome});
}
const extraNegatives=[];
for(const [id,input,reason] of [['prototype-id',{type:'select',id:'__proto__'},'unknown-entity'],['non-string-name',{type:'edit',id:'a',name:123},'invalid-name'],['unsupported-action',{type:'publish',id:'a'},'unsupported-action']]) {
 const before=structuredClone(state),result=transition(state,input);assert.equal(result.state,state);assert.deepEqual(state,before);assert.deepEqual(result.outcome,{accepted:false,reason});checks+=3;extraNegatives.push({id,input,rejected:true,reason});
}
const report={kind:'actual-node-pure-state-transitions-not-browser-dom-evidence',startedAt,completedAt:new Date().toISOString(),environment:{node:process.version,platform:process.platform,arch:process.arch},sourceHashes,states:STEPS.length,checks,passed:true,observations,extraNegatives};
const args=process.argv.slice(2);if(args.length){assert.equal(args[0],'--record');assert.equal(args.length,2);assert.match(args[1],/^[a-z][a-z0-9-]+$/);const dir=new URL('observations/'+args[1]+'/',root);await mkdir(new URL('observations/',root),{recursive:true});await mkdir(dir);await writeFile(new URL('node.json',dir),JSON.stringify(report,null,2)+'\n',{flag:'wx'});}console.log(JSON.stringify(report,null,2));
