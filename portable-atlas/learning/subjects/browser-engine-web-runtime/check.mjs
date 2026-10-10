import assert from 'node:assert/strict';import {readFile,mkdir,writeFile} from 'node:fs/promises';import {createHash} from 'node:crypto';import {compare,EXPECTED} from './oracle.mjs';import {SOURCES} from './sources.mjs';
const root=new URL('./',import.meta.url),hash=b=>createHash('sha256').update(b).digest('hex'),args=process.argv.slice(2);
const sourceHashes=Object.fromEntries(await Promise.all(SOURCES.map(async f=>[f,hash(await readFile(new URL(f,root)))])));
function checkRun(r){
 let checks=0;const test=(value)=>{assert.ok(value);checks++;};
 test(r.kind==='actual-browser-event-loop');test(Object.hasOwn(EXPECTED,r.input.caseId));test(/^\d+$/.test(r.input.runId));test(r.input.timerDelayMs===0);assert.deepEqual(r.sourceHashes,sourceHashes);checks++;
 test(r.loadedAt<=r.startedAt&&r.startedAt<=r.completedAt);test(Number.isFinite(Date.parse(r.startedAt)));test(r.environment.userAgent.includes('Mozilla/'));test(r.environment.language);test(Number.isFinite(r.environment.timeOrigin));test(r.loading.manifestStatus===200);test(r.loading.manifestContentType.startsWith('application/json'));test(r.loading.script==='case.mjs');test(r.loading.documentPath==='case.html?case='+r.input.caseId+'&run='+r.input.runId||r.loading.documentPath==='/case.html?case='+r.input.caseId+'&run='+r.input.runId);
 const c=compare(r.input.caseId,r.trace);test(c.passed);test(!c.wrongModelMatches);test(c.firstWrongIndex>=0);
 let last=-1;
 for(const [i,e] of r.trace.entries()){test(e.sequence===i+1);test(Number.isFinite(e.elapsedMs)&&e.elapsedMs>=last);test(Number.isFinite(Date.parse(e.at))&&e.at>=r.startedAt&&e.at<=r.completedAt);test(e.kind===(e.label.startsWith('sync-')?'sync':e.label.startsWith('timer-')&&e.label!=='timer-micro'?'timer-task':'microtask'));last=e.elapsedMs;}
 if(r.input.caseId==='caught-error'){assert.deepEqual(r.caught,{name:'Error',message:'intentional promise reaction failure'});checks++;}else{test(r.caught===null);}
 return checks;
}
// これは合成fixtureの検査で、Node event loopやBrowser実行の証拠ではない。
function synthetic(caseId){const at='2000-01-01T00:00:00.000Z';return {kind:'actual-browser-event-loop',input:{caseId,runId:'1',timerDelayMs:0},loadedAt:at,startedAt:at,completedAt:at,environment:{userAgent:'Mozilla/synthetic',language:'ja',timeOrigin:0},sourceHashes,loading:{manifestStatus:200,manifestContentType:'application/json',script:'case.mjs',documentPath:'/case.html?case='+caseId+'&run=1'},trace:EXPECTED[caseId].map((label,i)=>({label,sequence:i+1,at,elapsedMs:i,kind:label.startsWith('sync-')?'sync':label.startsWith('timer-')&&label!=='timer-micro'?'timer-task':'microtask'})),caught:caseId==='caught-error'?{name:'Error',message:'intentional promise reaction failure'}:null};}
const negatives=[];
for(const [id,mutate] of [
 ['deferred-child',r=>{[r.trace[4],r.trace[6]]=[r.trace[6],r.trace[4]];}],
 ['timer-before-sync-end',r=>{[r.trace[1],r.trace[6]]=[r.trace[6],r.trace[1]];}],
 ['missing-timer-micro',r=>r.trace.splice(7,1)],
 ['stale-source',r=>r.sourceHashes={...r.sourceHashes,'case.mjs':'0'.repeat(64)}],
 ['nonmonotonic-time',r=>r.trace[3].elapsedMs=-1],
 ['missing-loading-proof',r=>r.loading.manifestStatus=404]
]){const r=structuredClone(synthetic('nested'));mutate(r);assert.throws(()=>checkRun(r));negatives.push({id,rejected:true});}
const syntheticChecks=Object.keys(EXPECTED).reduce((n,id)=>n+checkRun(synthetic(id)),0);
const html=await readFile(new URL('index.html',root),'utf8'),readme=await readFile(new URL('README.md',root),'utf8'),scope=JSON.parse(await readFile(new URL('scope.json',root)));
const coverage=[...html.matchAll(/data-coverage="([^"]+)"/g)].flatMap(m=>m[1].split(' '));assert.equal([...html.matchAll(/data-coverage=/g)].length,4);assert.deepEqual([...new Set(coverage)].sort(),scope.unmade.map(x=>x.id).sort());for(const id of scope.unmade.map(x=>x.id))assert.ok(readme.includes(id));assert.ok(html.includes('id="learning-path"'));assert.ok(html.includes('id="next-experiments"'));
let localLinksChecked=0;for(const m of html.matchAll(/href="([^"]+)"/g)){if(m[1].startsWith('https:'))continue;const [f,frag]=m[1].split('#');if(!f)assert.ok(html.includes('id="'+frag+'"'));else if(f!=='sources.json')await readFile(new URL(f,root));localLinksChecked++;}
let browserChecks=0,actualRuns=0,artifacts={};
if(args[0]!=='--self-test'){
 const record=JSON.parse(await readFile(new URL('observations/browser-attempt-01/browser.json',root)));assert.equal(record.kind,'actual-iab-event-loop-qa');assert.deepEqual(record.runs.map(r=>r.input.caseId),['basic','nested','caught-error','nested']);assert.deepEqual(record.runs.map(r=>r.input.runId),['1','2','3','4']);
 browserChecks=record.runs.reduce((n,r)=>n+checkRun(r),0);actualRuns=record.runs.length;
 assert.deepEqual(record.answers.map(x=>x.value),['precision','fifo','checkpoint']);for(const a of record.answers){assert.ok(a.feedback.startsWith(a.value==='checkpoint'?'適切。':'不適切。'));assert.ok(a.snapshot);}
 assert.equal(record.prediction.value,'defer');assert.ok(record.prediction.snapshot);assert.equal(new Set(record.runs.map(r=>r.environment.timeOrigin)).size,4);
 for(const f of ['observations/browser-attempt-01/browser.json','observations/browser-attempt-01/nested.jpg','observations/browser-attempt-01/caught-error.jpg','observations/browser-attempt-01/roadmap.jpg','README.md','skills/atlas-browser-engine-web-runtime/SKILL.md']){const b=await readFile(new URL(f,root));artifacts[f]={bytes:b.length,sha256:hash(b)};}
}
const report={kind:args[0]==='--self-test'?'synthetic-oracle-self-test-not-runtime-evidence':'read-only-independent-browser-event-loop-checker',at:new Date().toISOString(),environment:{node:process.version,platform:process.platform,arch:process.arch},passed:true,actualRuns,browserChecks,syntheticChecks,negativeFixtures:negatives,roadmap:{experiments:4,unmadeCoverageIds:[...new Set(coverage)].sort(),localLinksChecked,executed:false},sourceHashes,checkerSha256:hash(await readFile(new URL('check.mjs',root))),artifacts,limitations:['No timer wall-clock accuracy assertion','Saved Browser trace check is not a new Browser execution','Synthetic checks are not Browser/Node event-loop evidence']};
if(args.length&&args[0]!=='--self-test'){assert.equal(args[0],'--record');assert.equal(args.length,2);assert.match(args[1],/^[a-z][a-z0-9-]+$/);const dir=new URL('observations/'+args[1]+'/',root);await mkdir(dir);await writeFile(new URL('check.json',dir),JSON.stringify(report,null,2)+'\n',{flag:'wx'});}else if(args[0]==='--self-test')assert.equal(args.length,1);
console.log(JSON.stringify(report,null,2));
