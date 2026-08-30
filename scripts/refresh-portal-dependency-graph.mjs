#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import { readFile, rename, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { auditPortalGraph, buildPortalGraph, resolveInputGroups } from './lib/portal-dependency-graph.mjs';

const root=process.cwd();const mode=process.argv[2]??'--record';const graphPath=path.join(root,'evidence/dependency-graph.json');const config=JSON.parse(await readFile(path.join(root,'contracts/portal-evidence-dependency-inputs.json'),'utf8'));const schema=JSON.parse(await readFile(path.join(root,'contracts/schemas/evidence-dependency-graph.schema.json'),'utf8'));
let previous=null;try{previous=JSON.parse(await readFile(graphPath,'utf8'));}catch{}

if(mode==='--check'){
  if(!previous)throw new Error('evidence/dependency-graph.jsonがありません');const result=await auditPortalGraph(root,previous,schema);console.log(`Portal Evidence Dependency Graph: ${result.ok?'PASS':'FAIL'} / inputs=${result.summary.inputs} changed=${result.summary.changedInputs} outputs=${result.summary.outputs} runs=${result.summary.runs} structures=${result.summary.structures}`);if(!result.ok){for(const error of result.errors)console.error(error);process.exitCode=1;}
}else if(mode==='--record'){
  const startedAt=new Date().toISOString();const inputs=await resolveInputGroups(root,config,previous,startedAt);const commands=[['import'],['non-regression'],['eval'],['sbom'],['build'],['perf'],['evidence'],['provenance']];
  for(const args of commands){const result=spawnSync('npm',['run',...args],{cwd:root,stdio:'inherit',env:{...process.env,PORTAL_DEPENDENCY_REFRESH:'1'}});if(result.status!==0)throw new Error(`npm run ${args.join(' ')} が失敗しました`);}
  const after=await resolveInputGroups(root,config,previous,startedAt);if(JSON.stringify(inputs.map((item)=>item.current_digest))!==JSON.stringify(after.map((item)=>item.current_digest)))throw new Error('再実行中にGraph入力が変化しました');
  const completedAt=new Date().toISOString();const runtimeIdentity={node:process.version,npm:spawnSync('npm',['--version'],{encoding:'utf8'}).stdout.trim(),os:`${os.platform()}-${os.release()}-${os.arch()}`,profile:'local'};const graph=await buildPortalGraph(root,{inputs,startedAt,completedAt,runtimeIdentity});const result=await auditPortalGraph(root,graph,schema);if(!result.ok)throw new Error(result.errors.join('; '));const temporary=`${graphPath}.tmp`;await writeFile(temporary,`${JSON.stringify(graph,null,2)}\n`);await rename(temporary,graphPath);console.log(`Portal Evidence Dependency Graph更新済み: inputs=${result.summary.inputs} changed=${result.summary.changedInputs} outputs=${result.summary.outputs}`);
}else throw new Error('使い方: refresh-portal-dependency-graph.mjs --record|--check');
