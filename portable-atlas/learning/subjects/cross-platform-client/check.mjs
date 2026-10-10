import assert from 'node:assert/strict';import {readFile,mkdir,writeFile} from 'node:fs/promises';import {createHash} from 'node:crypto';import {SOURCES} from './sources.mjs';import {vectors,expected} from './oracle.mjs';import {validate} from './validator.mjs';
const started=new Date().toISOString(),root=new URL('./',import.meta.url),hash=b=>createHash('sha256').update(b).digest('hex');
const sourceHashes=Object.fromEntries(await Promise.all(SOURCES.map(async f=>[f,hash(await readFile(new URL(f,root)))])));
const pythonFile='observations/python-attempt-04/raw.json',browserFile='observations/browser-attempt-02/raw.json';
const pythonBytes=await readFile(new URL(pythonFile,root)),python=JSON.parse(pythonBytes),browser=JSON.parse(await readFile(new URL(browserFile,root)));
let checks=0;const eq=(a,b)=>{assert.deepEqual(a,b);checks++;};
function times(r){assert(Number.isFinite(Date.parse(r.started))&&Date.parse(r.completed)>=Date.parse(r.started));checks++;}
function evidence(p,b){
  eq(p.kind,'actual-python-stdlib');eq(p.attempt,1);eq(p.retries,0);eq(p.sourceHashes,sourceHashes);eq(p.inputDigest,sourceHashes['vectors.json']);times(p);assert(p.environment.version&&p.environment.implementation==='CPython');checks++;
  eq(p.results.length,vectors.length);
  for(let i=0;i<vectors.length;i++){eq(p.results[i].id,vectors[i].id);eq(p.results[i].input,vectors[i].input);eq(p.results[i].result,expected(vectors[i].id,'python'));}
  eq(b.kind,'actual-iab-ui-qa');times(b);eq(b.observations.map(o=>o.name),['ascii-boundary','emoji-mismatch','emoji-boundary','invalid-surrogate','all-vectors','skill-normal-keyboard']);
  for(const o of b.observations){const r=JSON.parse(o.rawText);eq(r,o.raw);times(r);eq(r.kind,'actual-browser-js-vs-saved-python');eq(r.sourceHashes,sourceHashes);eq(r.inputDigest,sourceHashes['vectors.json']);eq(r.pythonArtifactDigest,hash(pythonBytes));assert(r.environment.userAgent.includes('Chrome/')&&r.environment.viewport.width>0);checks++;
    const ids={ 'ascii-boundary':['ascii-four'],'emoji-mismatch':['emoji-three'],'emoji-boundary':['emoji-four'],'invalid-surrogate':['lone-surrogate'],'all-vectors':vectors.map(v=>v.id),'skill-normal-keyboard':['emoji-two']}[o.name];
    eq(r.action,o.name==='all-vectors'?'all':'selected');eq(r.results.map(v=>v.id),ids);eq(o.rowCount,ids.length);assert(o.status.startsWith('比較完了：')&&o.answer);checks++;
    const expectedCells=[];
    for(const v of r.results){eq(v.input,vectors.find(x=>x.id===v.id).input);eq(v.result,expected(v.id,'browser'));eq(v.pythonResult,expected(v.id,'python'));const j=expected(v.id,'browser'),p=expected(v.id,'python'),yes=x=>x?'許可':'拒否';expectedCells.push([v.id,String(j.utf16Units??'拒否'),String(j.codePoints??'拒否'),String(j.utf8Bytes??'拒否'),yes(j.legacyAccepted),yes(p.legacyAccepted),`${yes(j.codePointAccepted)} / ${yes(p.codePointAccepted)}`,yes(j.byteAccepted)]);}
    eq(o.cells,expectedCells);
  }
  eq(b.skillRoutes.normal.mode,'same-agent');eq(b.skillRoutes.normal.supported,true);eq(b.skillRoutes.unsupported.supported,false);eq(b.skillRoutes.unsupported.nativeExecuted,false);
}
evidence(python,browser);
for(const v of vectors)eq(validate(v.input),expected(v.id,'browser'));
const negatives=[
  ['wrong-codepoint',(p,b)=>{b.observations[1].raw.results[0].result.codePoints=6;}],
  ['wrong-byte-unit',(p,b)=>{b.observations[1].raw.results[0].result.byteAccepted=true;}],
  ['stale-source',(p)=>{p.sourceHashes['validator.mjs']='0'.repeat(64);}],
  ['missing-vector',(p,b)=>{b.observations[4].raw.results.pop();}],
  ['invented-python-digest',(p,b)=>{b.observations[0].raw.pythonArtifactDigest='0'.repeat(64);}],
  ['missing-timestamp',(p,b)=>{b.observations[0].raw.started='unknown';}],
  ['unsafe-surrogate-acceptance',(p,b)=>{b.observations[3].raw.results[0].result.codePointAccepted=true;}]
];
for(const [name,mutate] of negatives){const p=structuredClone(python),b=structuredClone(browser);mutate(p,b);for(const o of b.observations)o.rawText=JSON.stringify(o.raw);assert.throws(()=>evidence(p,b),undefined,name);}
for(const o of browser.observations){assert(/^observations\/browser-attempt-02\/[a-z-]+\.jpg$/.test(o.screenshot));const bytes=await readFile(new URL(o.screenshot,root));eq(hash(bytes),o.screenshotDigest);assert(bytes.length>1000&&bytes[0]===255&&bytes[1]===216);checks++;}
const report={kind:'read-only-cross-runtime-check',started,completed:new Date().toISOString(),sourceHashes,pythonArtifact:{path:pythonFile,sha256:hash(pythonBytes)},browserArtifact:{path:browserFile,sha256:hash(await readFile(new URL(browserFile,root)))},checks,negativeFixtures:negatives.map(([name])=>({name,rejected:true})),subjectStatus:'incomplete'};
const args=process.argv.slice(2);if(args.length){assert(args.length===2&&args[0]==='--record'&&/^observations\/[a-z0-9-]+$/.test(args[1]));const d=new URL(args[1]+'/',root);await mkdir(d);await writeFile(new URL('raw.json',d),JSON.stringify(report,null,2)+'\n',{flag:'wx'});}
console.log(JSON.stringify(report));
