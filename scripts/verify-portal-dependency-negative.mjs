#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import { cp, mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { aggregateMemberDigest } from './lib/portal-dependency-graph.mjs';

const root=process.cwd();const coreDir=path.resolve(process.env.ATLAS_CORE_DIR??path.join(root,'..','reference-atlas-core'));const lock=JSON.parse(await readFile(path.join(root,'contracts/evidence-dependency-lock.json'),'utf8'));const fixture=JSON.parse(await readFile(path.join(root,'fixtures/evidence-dependency/digest-only-closure.json'),'utf8'));const graph=JSON.parse(await readFile(path.join(root,'evidence/dependency-graph.json'),'utf8'));
const coreHead=spawnSync('git',['rev-parse','HEAD'],{cwd:coreDir,encoding:'utf8'});if(coreHead.status!==0||coreHead.stdout.trim()!==lock.coreCommit)throw new Error(`Core checkoutが固定commitではありません: ${coreHead.stdout.trim()}`);
const temporary=await mkdtemp(path.join(os.tmpdir(),'portal-dependency-negative-'));
try{
  const required=new Set(['evidence/dependency-graph.json']);for(const input of graph.inputs)for(const member of input.members)required.add(member);for(const output of graph.outputs)required.add(output.path);for(const structure of graph.structures)required.add(structure.path);const index=JSON.parse(await readFile(path.join(root,'evidence/scenarios/index.json'),'utf8'));for(const item of index.files??[])required.add(item.path);
  for(const relative of required){await mkdir(path.dirname(path.join(temporary,relative)),{recursive:true});await cp(path.join(root,relative),path.join(temporary,relative));}
  const input=graph.inputs.find((item)=>item.kind===fixture.inputKind);if(!input)throw new Error(`negative fixture input kindがありません: ${fixture.inputKind}`);const member=input.members[0];const bytes=await readFile(path.join(temporary,member));await writeFile(path.join(temporary,member),Buffer.concat([bytes,Buffer.from(fixture.memberAppend)]));input.current_digest=await aggregateMemberDigest(temporary,input.members);const run=graph.runs.find((item)=>item.id==='portal-reproduce-run');const completed=new Date(run.completed_at);input.observed_at=new Date(completed.getTime()+fixture.observedAfterRunSeconds*1000).toISOString();const binding=run.input_bindings.find((item)=>item.input_id===input.id);binding.digest=input.current_digest;await writeFile(path.join(temporary,'evidence/dependency-graph.json'),`${JSON.stringify(graph,null,2)}\n`);
  const result=spawnSync('go',['run','./cmd/atlas','audit',temporary,'--gate','evidence-dependency'],{cwd:coreDir,encoding:'utf8'});const combined=`${result.stdout??''}${result.stderr??''}`;if(result.status!==fixture.expectedExitCode||!combined.includes(fixture.expectedDiagnostic))throw new Error(`digest-only負例が期待どおり拒否されません: exit=${result.status} output=${combined}`);console.log(`Portal Evidence Dependency negative: PASS / Core ${lock.coreCommit.slice(0,12)} / ${fixture.expectedDiagnostic}`);
}finally{await rm(temporary,{recursive:true,force:true});}
