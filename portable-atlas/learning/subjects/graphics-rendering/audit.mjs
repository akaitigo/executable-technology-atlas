import assert from 'node:assert/strict';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const root=new URL('./',import.meta.url);
const hash=b=>createHash('sha256').update(b).digest('hex');
const cpuBytes=await readFile(new URL('observations/cpu-attempt-01/run.json',root));
const cpu=JSON.parse(cpuBytes), cpuHash=hash(cpuBytes);
const browserBytes=await readFile(new URL('observations/browser-attempt-01/browser.json',root));
const browser=JSON.parse(browserBytes);
for(const [file,digest] of Object.entries(cpu.sourceHashes))assert.equal(hash(await readFile(new URL(file,root))),digest,`stale source ${file}`);
for(const [file,info] of Object.entries(cpu.artifacts))assert.equal(hash(await readFile(new URL('observations/cpu-attempt-01/'+file,root))),info.sha256,file);
function check(record){
  assert.equal(record.kind,'actual-iab-cpu-png-sampling');assert.equal(record.observations.length,19);
  const expectedIds=[...cpu.results.map(c=>c.id),'shared-edge-center','invalid-x','invalid-y','invalid-fraction','invalid-empty','last-pixel','answer-order','answer-depth','answer-gpu'];
  assert.deepEqual(record.observations.map(o=>o.id),expectedIds);
  let checks=0;
  for(const obs of record.observations){
    const s=obs.state;assert.ok(obs.input&&obs.snapshot&&obs.at);assert.equal(s.runSha256,cpuHash);assert.deepEqual(s.sourceHashes,cpu.sourceHashes);assert.equal(s.ready,true);assert.equal(s.loading,false);checks+=5;
    if(obs.id.startsWith('invalid-')){assert.equal(s.sample.rejected,true);checks++;continue;}
    const sample=s.sample,scene=cpu.results.find(c=>c.id===s.caseId);assert.ok(scene);assert.equal(sample.caseId,s.caseId);assert.ok(Number.isInteger(sample.x)&&Number.isInteger(sample.y));checks+=3;
    for(const mode of ['depth','painter']){
      const p=scene[mode].pixels[sample.y*16+sample.x];
      assert.equal(sample[mode].owner,p.owner);assert.equal(sample[mode].depthExact,p.depthExact);assert.deepEqual(sample[mode].pythonRgb,p.rgb);assert.deepEqual(sample[mode].decodedRgba,[...p.rgb,255]);assert.deepEqual(sample[mode].fragments,p.fragments);assert.equal(sample[mode].matched,true);assert.equal(obs[mode+'Src'],`observations/cpu-attempt-01/${scene.id}-${mode}.png`);checks+=7;
    }
    if(obs.id.startsWith('answer-')){const prefix=({'answer-order':'不足。','answer-depth':'適切。','answer-gpu':'未検証。'})[obs.id];assert.ok(s.feedback.startsWith(prefix));checks++;}
  }
  const center=record.observations.find(o=>o.id==='shared-edge-center').state.sample;
  assert.deepEqual([center.x,center.y],[5,5]);assert.equal(center.depth.fragments.filter(f=>f.covered).length,1);checks+=2;
  return checks;
}
const checks=check(browser);
const negatives=[];
for(const [id,mutate] of [
  ['wrong-decoded-pixel',r=>r.observations[0].state.sample.depth.decodedRgba[0]=0],
  ['stale-cpu-binding',r=>r.observations[0].state.runSha256='0'.repeat(64)],
  ['wrong-scene-output',r=>r.observations[0].depthSrc='observations/cpu-attempt-01/normal-ba-depth.png']
]){const r=structuredClone(browser);mutate(r);assert.throws(()=>check(r));negatives.push({id,rejected:true});}
const artifacts={};
for(const file of ['observations/cpu-attempt-01/run.json','observations/browser-attempt-01/browser.json','observations/browser-attempt-01/comparison.jpg','observations/browser-attempt-01/comparison-detail.jpg','skills/atlas-graphics-rendering/SKILL.md']){const bytes=await readFile(new URL(file,root));artifacts[file]={sha256:hash(bytes),bytes:bytes.length};}
const result={at:new Date().toISOString(),kind:'read-only-cpu-browser-artifact-check',environment:{node:process.version,platform:process.platform,arch:process.arch},checks,observations:19,passed:true,auditorSha256:hash(await readFile(new URL('audit.mjs',root))),sourceHashes:cpu.sourceHashes,negativeFixtures:negatives,artifacts};
const args=process.argv.slice(2);
if(args.length){assert.equal(args[0],'--record');assert.equal(args.length,2);assert.match(args[1],/^[a-z][a-z0-9-]+$/);const dir=new URL('observations/'+args[1]+'/',root);await mkdir(dir);await writeFile(new URL('audit.json',dir),JSON.stringify(result,null,2)+'\n',{flag:'wx'});}
console.log(JSON.stringify(result,null,2));
