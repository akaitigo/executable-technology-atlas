import assert from 'node:assert/strict';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {SOURCES} from './sources.mjs';
const root=new URL('./',import.meta.url),hash=b=>createHash('sha256').update(b).digest('hex');
const sources=Object.fromEntries(await Promise.all(SOURCES.map(async f=>[f,hash(await readFile(new URL(f,root)))])));
const bytes=await readFile(new URL('observations/browser-attempt-02/browser.json',root)),record=JSON.parse(bytes);
const expected=[['initial',0],['a-increment',1],['b-increment',2],['zero',2],['assign-import',2],['assign-namespace',2],['reimport',2],['invalid',2],['minus',1],['failure-loading',1],['failure-syntax',1],['after-failure-increment',2],['answer-snapshot',2],['answer-live',2],['answer-assign',2]];
function check(r){
  assert.equal(r.kind,'actual-iab-native-es-modules');assert.deepEqual(r.observations.map(o=>o.id),expected.map(e=>e[0]));let checks=2;
  for(let i=0;i<expected.length;i++){
    const [id,value]=expected[i],o=r.observations[i],s=o.state;
    assert.ok(o.input&&o.snapshot&&o.at);assert.equal(s.ready,true);assert.deepEqual(s.sourceHashes,sources);assert.deepEqual(s.views,{a:{live:value,snapshot:0},b:{live:value,snapshot:0}});assert.equal(s.namespaceSame,true);checks+=5;
    for(const module of ['counter','importer-a','importer-b']){assert.equal(s.journal.evaluationCounts[module],1);assert.equal(s.journal.events.filter(e=>e.type==='module-evaluated'&&e.detail.module===module).length,1);checks+=2;}
    const since=i?r.observations[i-1].at:null;
    const fresh=s.journal.events.filter(e=>(!since||e.at>since)&&e.at<=o.at);
    if(['a-increment','b-increment','zero','minus','after-failure-increment'].includes(id)){
      const expectedAction=id==='after-failure-increment'?'a-increment':id;
      assert.equal(s.lastAction.id,expectedAction);assert.ok(fresh.some(e=>e.type==='counter-mutation'));assert.ok(fresh.some(e=>e.type==='ui-action'&&e.detail.id===expectedAction));checks+=3;
    }
    if(id==='assign-import'||id==='assign-namespace'){assert.equal(s.lastAssignment.id,id);assert.equal(s.lastAssignment.name,'TypeError');assert.equal(s.lastAssignment.rejected,true);assert.ok(fresh.some(e=>e.type.endsWith('assignment-rejected')));checks+=4;}
    if(id==='reimport'){assert.equal(s.lastAction.id,id);assert.deepEqual(s.lastAction.result,{sameNamespace:true,live:2,ordinal:1});assert.ok(fresh.some(e=>e.type==='ui-action'&&e.detail.id===id));checks+=3;}
    if(id==='invalid'){assert.equal(s.lastAction.rejected,true);assert.equal(s.lastAction.name,'RangeError');assert.ok(fresh.some(e=>e.type==='ui-rejection'&&e.detail.id===id));checks+=3;}
    if(id.startsWith('failure-')){assert.ok(fresh.some(e=>e.type==='isolated-fixture-requested'&&e.detail.caseId===id.slice(8)));checks++;}
    if(id.startsWith('answer-')){const answer=id.slice(7),prefix=({snapshot:'不足。',live:'適切。',assign:'不適切。'})[answer];assert.ok(s.feedback.startsWith(prefix));assert.ok(fresh.some(e=>e.type==='answer'&&e.detail.value===answer));checks+=2;}
  }
  assert.equal(r.isolatedFailures.length,2);checks++;
  for(const [id,name,status,mime] of [['loading','TypeError',404,'text/plain'],['syntax','SyntaxError',200,'text/javascript']]){
    const f=r.isolatedFailures.find(f=>f.caseId===id);assert.ok(f);assert.equal(f.kind,'actual-browser-isolated-module-failure');assert.equal(f.result.failed,true);assert.equal(f.result.name,name);assert.equal(f.http.status,status);assert.ok(f.http.contentType.startsWith(mime));assert.ok(f.startedAt<=f.completedAt);assert.deepEqual(f.sourceHashes,sources);checks+=8;
  }
  return checks;
}
const checks=check(record),negatives=[];
for(const [id,mutate] of [
 ['copied-value-is-not-live',r=>r.observations[2].state.views.b.snapshot=2],
 ['second-counter-evaluation',r=>r.observations[6].state.journal.evaluationCounts.counter=2],
 ['loading-is-not-syntax',r=>r.isolatedFailures[0].result.name='SyntaxError'],
 ['stale-source-binding',r=>r.observations[0].state.sourceHashes['counter.mjs']='0'.repeat(64)]
]){const clone=structuredClone(record);mutate(clone);assert.throws(()=>check(clone));negatives.push({id,rejected:true});}
const node=JSON.parse(await readFile(new URL('observations/node-attempt-03/node.json',root)));assert.deepEqual(node.sourceHashes,sources);assert.equal(node.kind,'actual-node-file-module-loader-not-browser-evidence');assert.equal(node.failures[0].code,'ERR_MODULE_NOT_FOUND');
const html=await readFile(new URL('index.html',root),'utf8'),readme=await readFile(new URL('README.md',root),'utf8'),scope=JSON.parse(await readFile(new URL('scope.json',root),'utf8'));
const coverage=[...html.matchAll(/data-coverage="([^"]+)"/g)].flatMap(m=>m[1].split(' '));assert.equal([...html.matchAll(/data-coverage=/g)].length,4);
assert.deepEqual([...new Set(coverage)].sort(),scope.unmade.map(x=>x.id).sort());
for(const id of ['learning-path','next-experiments'])assert.ok(html.includes(`id="${id}"`));
for(const id of scope.unmade.map(x=>x.id))assert.ok(readme.includes(id));
let localLinksChecked=0;
for(const match of html.matchAll(/href="([^"]+)"/g)){
 const url=match[1];if(url.startsWith('https:'))continue;
 const [file,fragment]=url.split('#');
 if(!file){assert.ok(html.includes(`id="${fragment}"`));}else if(file!=='sources.json'){await readFile(new URL(file,root));}
 localLinksChecked++;
}
const artifacts={};
for(const f of ['observations/browser-attempt-02/browser.json','observations/browser-attempt-02/live-binding.jpg','observations/browser-attempt-02/isolated-failures.jpg','observations/browser-attempt-02/roadmap.jpg','observations/node-attempt-03/node.json','skills/atlas-frontend-platform/SKILL.md','README.md']){const b=await readFile(new URL(f,root));artifacts[f]={bytes:b.length,sha256:hash(b)};}
const report={kind:'read-only-independent-browser-module-oracle',at:new Date().toISOString(),environment:{node:process.version,platform:process.platform,arch:process.arch},observations:15,isolatedFailures:2,checks,roadmap:{plannedExperiments:4,unmadeCoverageIds:[...new Set(coverage)].sort(),localLinksChecked,executed:false},passed:true,sourceHashes:sources,auditorSha256:hash(await readFile(new URL('audit.mjs',root))),negativeFixtures:negatives,artifacts,limitations:['Saved Browser result checking is not a fresh Browser execution','Node loader observations are separate and not substituted for Browser behavior']};
const args=process.argv.slice(2);
if(args.length){assert.equal(args[0],'--record');assert.equal(args.length,2);assert.match(args[1],/^[a-z][a-z0-9-]+$/);const dir=new URL('observations/'+args[1]+'/',root);await mkdir(dir);await writeFile(new URL('audit.json',dir),JSON.stringify(report,null,2)+'\n',{flag:'wx'});}
console.log(JSON.stringify(report,null,2));
