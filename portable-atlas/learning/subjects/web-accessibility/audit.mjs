import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const root=new URL('./',import.meta.url);
const hash=b=>createHash('sha256').update(b).digest('hex');
const browserBytes=await readFile(new URL('observations/browser-attempt-01/browser.json',root));
const record=JSON.parse(browserBytes);
const sourceHashes=Object.fromEntries(await Promise.all(Object.keys(record.sourceHashes).map(async f=>[f,hash(await readFile(new URL(f,root)))])));
assert.deepEqual(record.sourceHashes,sourceHashes,'captured source changed');
// Stronger temporal oracle, independent of the lesson reducer: each input needs
// fresh trusted events from its own observation interval, not an earlier key.
function fresh(r,id){const i=r.observations.findIndex(o=>o.id===id);assert.ok(i>=0,id);const o=r.observations[i];const since=i?r.observations[i-1].at:r.startedAt;return o.events.filter(e=>e.at>since&&e.at<=o.at);}
function audit(r){
  const keys={'native-enter':['native','Enter'],'native-space':['native',' '],'role-only-enter':['custom','Enter'],'role-only-space':['custom',' '],'repaired-enter':['custom','Enter'],'repaired-space':['custom',' '],'disabled-enter':['custom','Enter'],'disabled-space':['custom',' '],'name-missing-keyboard':['unnamed','Enter']};
  for(const [id,[target,key]] of Object.entries(keys))for(const type of ['keydown','keyup'])assert.ok(fresh(r,id).some(e=>e.trusted&&e.id===target&&e.key===key&&e.type===type),`${id} missing fresh ${type}`);
  const tabs={'native-tab':['start','native'],'click-only-tab-skips':['native','end'],'role-only-tab':['native','custom'],'repaired-tab':['native','custom'],'disabled-tab':['start','custom']};
  for(const [id,[from,to]] of Object.entries(tabs)){
    const events=fresh(r,id);assert.ok(events.some(e=>e.trusted&&e.type==='keydown'&&e.key==='Tab'&&e.id===from),`${id} Tab`);
    assert.ok(events.some(e=>e.trusted&&e.type==='focusin'&&e.id===to),`${id} focus`);
  }
  for(const id of ['click-only-mouse','disabled-mouse'])assert.ok(fresh(r,id).some(e=>e.trusted&&e.type==='click'&&e.id==='custom'),`${id} click`);
  for(const id of ['repaired-space','disabled-space'])for(const type of ['keydown','keyup'])assert.ok(fresh(r,id).some(e=>e.type===type&&e.key===' '&&e.prevented),`${id} prevent scroll`);
  for(const id of ['role-only-enter','role-only-space'])assert.equal(r.observations.find(o=>o.id===id).customCount,0);
  assert.equal(r.observations.find(o=>o.id==='name-missing').unnamedEmptyCount,1);
  assert.equal(r.observations.find(o=>o.id==='name-restored').unnamedNamedCount,1);
}
audit(record);
const negatives=[];
for(const [id,mutate] of [
  ['prior-keys-are-not-proof',r=>r.observations.find(o=>o.id==='disabled-enter').events=r.observations.find(o=>o.id==='disabled-tab').events],
  ['focus-transition-required',r=>{const o=r.observations.find(o=>o.id==='click-only-tab-skips');o.events=o.events.filter(e=>e.type!=='focusin');}],
  ['name-fix-cannot-be-label-inference',r=>r.observations.find(o=>o.id==='name-restored').unnamedNamedCount=0]
]){const copy=structuredClone(record);mutate(copy);assert.throws(()=>audit(copy));negatives.push({id,rejected:true});}
const artifacts={};
for(const f of ['observations/browser-attempt-01/browser.json','observations/browser-attempt-01/browser.partial.json','observations/browser-attempt-01/comparison.jpg','observations/browser-attempt-01/name-missing.jpg','observations/checked-attempt-01/node.json','skills/atlas-web-accessibility/SKILL.md']){
  const bytes=await readFile(new URL(f,root));artifacts[f]={bytes:bytes.length,sha256:hash(bytes)};
}
const report={at:new Date().toISOString(),kind:'read-only-temporal-evidence-audit',sourceHashes,auditorSha256:hash(await readFile(new URL('audit.mjs',root))),browserSha256:hash(browserBytes),passed:true,keyIntervals:9,tabTransitions:5,mouseIntervals:2,negativeFixtures:negatives,artifacts};
const args=process.argv.slice(2);
if(args.length){assert.equal(args[0],'--record');assert.equal(args.length,2);assert.match(args[1],/^[a-z][a-z0-9-]+$/);const dir=new URL('observations/'+args[1]+'/',root);await mkdir(dir);await writeFile(new URL('audit.json',dir),JSON.stringify(report,null,2)+'\n',{flag:'wx'});}
console.log(JSON.stringify(report,null,2));
