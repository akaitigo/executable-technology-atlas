#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import { cp, mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { resolveCoreCheckout } from './lib/core-checkout.mjs';
import { aggregateMemberDigest, buildPortalGraph, discoverPortalOutputs, resolveInputGroups } from './lib/portal-dependency-graph.mjs';

const root=process.cwd();const lock=JSON.parse(await readFile(path.join(root,'contracts/evidence-dependency-lock.json'),'utf8'));const {coreDir}=resolveCoreCheckout(root,lock.coreCommit);const fixture=JSON.parse(await readFile(path.join(root,'fixtures/evidence-dependency/digest-only-closure.json'),'utf8'));const previousGraph=JSON.parse(await readFile(path.join(root,'evidence/dependency-graph.json'),'utf8'));const config=JSON.parse(await readFile(path.join(root,'contracts/portal-evidence-dependency-inputs.json'),'utf8'));
const taskGoCache=path.join(os.tmpdir(),'atlas-portal-go-build-cache');
const temporary=await mkdtemp(path.join(os.tmpdir(),'portal-dependency-negative-'));
try{
  const resolvedRootInputs=await resolveInputGroups(root,config,previousGraph,previousGraph.runs.find((item)=>item.id==='portal-reproduce-run')?.started_at??'2026-08-31T00:00:00.000Z');
  const required=new Set();for(const input of resolvedRootInputs)for(const member of input.members)required.add(member);for(const output of await discoverPortalOutputs(root))required.add(output);required.add('evidence/scenarios/index.json');required.add('evidence/scenarios/closure-plan.json');const index=JSON.parse(await readFile(path.join(root,'evidence/scenarios/index.json'),'utf8'));for(const item of index.files??[])required.add(item.path);
  for(const relative of required){await mkdir(path.dirname(path.join(temporary,relative)),{recursive:true});await cp(path.join(root,relative),path.join(temporary,relative));}
  const run=previousGraph.runs.find((item)=>item.id==='portal-reproduce-run');const startedAt=run?.started_at??'2026-08-31T00:00:00.000Z';const completedAt=run?.completed_at??'2026-08-31T00:00:01.000Z';const runtimeIdentity=run?.runtime_identity??{node:process.version,npm:'unknown',os:'unknown',profile:'local'};
  const inputs=await resolveInputGroups(temporary,config,previousGraph,startedAt);const graph=await buildPortalGraph(temporary,{inputs,startedAt,completedAt,runtimeIdentity});
  const input=graph.inputs.find((item)=>item.kind===fixture.inputKind);if(!input)throw new Error(`negative fixture input kindがありません: ${fixture.inputKind}`);const member=input.members[0];const bytes=await readFile(path.join(temporary,member));await writeFile(path.join(temporary,member),Buffer.concat([bytes,Buffer.from(fixture.memberAppend)]));input.current_digest=await aggregateMemberDigest(temporary,input.members);const completed=new Date(completedAt);input.observed_at=new Date(completed.getTime()+fixture.observedAfterRunSeconds*1000).toISOString();const binding=graph.runs.find((item)=>item.id==='portal-reproduce-run')?.input_bindings.find((item)=>item.input_id===input.id);binding.digest=input.current_digest;await writeFile(path.join(temporary,'evidence/dependency-graph.json'),`${JSON.stringify(graph,null,2)}\n`);
  const result=spawnSync('go',['run','./cmd/atlas','audit',temporary,'--gate','evidence-dependency'],{cwd:coreDir,encoding:'utf8',env:{...process.env,GOCACHE:taskGoCache}});const combined=`${result.stdout??''}${result.stderr??''}`;if(result.status!==fixture.expectedExitCode||!combined.includes(fixture.expectedDiagnostic))throw new Error(`digest-only負例が期待どおり拒否されません: exit=${result.status} output=${combined}`);console.log(`Portal Evidence Dependency negative: PASS / Core ${lock.coreCommit.slice(0,12)} / ${fixture.expectedDiagnostic}`);
}finally{await rm(temporary,{recursive:true,force:true});}
