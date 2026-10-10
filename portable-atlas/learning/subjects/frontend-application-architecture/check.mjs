import assert from 'node:assert/strict';import {readFile,mkdir,writeFile} from 'node:fs/promises';import {createHash} from 'node:crypto';import {STEPS} from './oracle.mjs';import {SOURCES} from './sources.mjs';
const root=new URL('./',import.meta.url),hash=b=>createHash('sha256').update(b).digest('hex');
const sourceHashes=Object.fromEntries(await Promise.all(SOURCES.map(async f=>[f,hash(await readFile(new URL(f,root)))])));
function domFor(v){return Object.fromEntries(['duplicated','normalized'].map(mode=>{const m=v[mode];return [mode,{list:m.list.length?m.list.map(e=>e.id+': '+e.name):['entityなし'],detail:m.detail?m.detail.id+': '+m.detail.name:'未選択',selected:'selectedId: '+(m.selectedId??'null'),drift:'保存データ差分ID: '+(m.driftIds.join(', ')||'なし')}];}));}
function check(r){
 let count=0;assert.equal(r.kind,'actual-iab-state-ownership-qa');assert.deepEqual(r.observations.map(o=>o.id),STEPS.map(s=>s.id));count+=2;
 for(const [i,step] of STEPS.entries()){
  const o=r.observations[i],s=o.raw;assert.ok(o.at&&o.snapshot);assert.equal(s.kind,'actual-browser-normalized-state-ui');assert.deepEqual(s.sourceHashes,sourceHashes);assert.deepEqual(s.state,step.state);assert.deepEqual(s.views,step.views);assert.deepEqual(o.dom,domFor(step.views));assert.equal(s.events.length,i);count+=7;
  for(const id of ['duplicated','normalized']){assert.ok(o.snapshot.includes(o.dom[id].detail));count++;}
  if(i){const e=s.events.at(-1);assert.equal(e.sequence,i);assert.deepEqual(e.input,step.input);assert.deepEqual(e.before,STEPS[i-1].state);assert.deepEqual(e.after,step.state);assert.deepEqual(e.outcome,step.outcome);assert.ok(e.startedAt<=e.completedAt&&e.completedAt<=o.at);assert.ok(!r.observations[i-1].at||e.startedAt>=r.observations[i-1].at);count+=7;}
 }
 assert.deepEqual(r.answers.map(a=>a.value),['copies','normalize','global']);count++;
 for(const a of r.answers){assert.ok(a.snapshot&&a.raw.sourceHashes);assert.equal(a.raw.actions.at(-1).value,a.value);assert.deepEqual(a.raw.sourceHashes,sourceHashes);assert.equal(a.feedback,a.raw.feedback);assert.ok(a.feedback.startsWith(({copies:'不十分。',normalize:'適切。',global:'不適切。'})[a.value]));count+=5;}
 assert.equal(r.prediction.value,'copies');assert.ok(r.prediction.snapshot.includes('予想を保存: copies'));count+=2;
 return count;
}
const record=JSON.parse(await readFile(new URL('observations/browser-attempt-01/browser.json',root))),checks=check(record),negativeFixtures=[];
for(const [id,mutate] of [
 ['hide-copy-drift',r=>r.observations[1].raw.views.duplicated.driftIds=[]],
 ['stale-normalized-list',r=>r.observations[1].dom.normalized.list[0]='a: Alpha'],
 ['accept-unknown-id',r=>r.observations[7].raw.events.at(-1).outcome.accepted=true],
 ['keep-dangling-selection',r=>r.observations[10].raw.state.normalized.selectedId='b'],
 ['fake-source-binding',r=>r.observations[0].raw.sourceHashes['model.mjs']='0'.repeat(64)],
 ['missing-input-trace',r=>r.observations[4].raw.events.at(-1).input=null]
]){const changed=structuredClone(record);mutate(changed);assert.throws(()=>check(changed));negativeFixtures.push({id,rejected:true});}
const node=JSON.parse(await readFile(new URL('observations/node-attempt-01/node.json',root)));assert.equal(node.kind,'actual-node-pure-state-transitions-not-browser-dom-evidence');assert.deepEqual(node.sourceHashes,sourceHashes);assert.equal(node.passed,true);
const html=await readFile(new URL('index.html',root),'utf8'),readme=await readFile(new URL('README.md',root),'utf8'),scope=JSON.parse(await readFile(new URL('scope.json',root)));
const coverage=[...html.matchAll(/data-coverage="([^"]+)"/g)].flatMap(m=>m[1].split(' '));assert.equal([...html.matchAll(/data-coverage=/g)].length,4);assert.deepEqual([...new Set(coverage)].sort(),scope.unmade.map(x=>x.id).sort());for(const id of scope.unmade.map(x=>x.id))assert.ok(readme.includes(id));for(const id of ['learning-path','next-experiments','ownership-diagram'])assert.ok(html.includes('id="'+id+'"'));
assert.equal(record.roadmap.rows.length,4);assert.deepEqual([...new Set(record.roadmap.rows.flatMap(row=>row.coverage.split(' ')))].sort(),scope.unmade.map(x=>x.id).sort());
let localLinksChecked=0;for(const m of html.matchAll(/href="([^"]+)"/g)){if(m[1].startsWith('https:'))continue;const [f,fragment]=m[1].split('#');if(!f)assert.ok(html.includes('id="'+fragment+'"'));else if(f!=='sources.json')await readFile(new URL(f,root));localLinksChecked++;}
const artifacts={};for(const f of ['observations/browser-attempt-01/browser.json','observations/browser-attempt-01/state-drift.jpg','observations/browser-attempt-01/empty-boundary.jpg','observations/browser-attempt-01/roadmap.jpg','observations/node-attempt-01/node.json','README.md','skills/atlas-frontend-application-architecture/SKILL.md']){const b=await readFile(new URL(f,root));artifacts[f]={bytes:b.length,sha256:hash(b)};}
const report={kind:'read-only-independent-state-ownership-dom-oracle',at:new Date().toISOString(),environment:{node:process.version,platform:process.platform,arch:process.arch},passed:true,states:17,checks,negativeFixtures,sourceHashes,checkerSha256:hash(await readFile(new URL('check.mjs',root))),roadmap:{experiments:4,unmadeCoverageIds:[...new Set(coverage)].sort(),localLinksChecked,executed:false},artifacts,limitations:['Saved Browser checking is not new Browser execution','Node pure model test is not Browser DOM evidence','React/Redux are concept references, not executed products']};
const args=process.argv.slice(2);if(args.length){assert.equal(args[0],'--record');assert.equal(args.length,2);assert.match(args[1],/^[a-z][a-z0-9-]+$/);const dir=new URL('observations/'+args[1]+'/',root);await mkdir(new URL('observations/',root),{recursive:true});await mkdir(dir);await writeFile(new URL('check.json',dir),JSON.stringify(report,null,2)+'\n',{flag:'wx'});}console.log(JSON.stringify(report,null,2));
