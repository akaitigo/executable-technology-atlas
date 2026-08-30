import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { readdir, readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { canonicalJson, sha256 } from './crypto.mjs';

const POLICY={transitive_staleness:true,digest_only_closure_forbidden:true,actual_rerun_required:true,missing_rerun_targets_fail:true,proof_structure_invariant:true,closure_plan_structure_invariant:true};

async function walkFiles(root,relative){
  const base=path.join(root,relative);const entries=await readdir(base,{withFileTypes:true});const result=[];
  for(const entry of entries.sort((a,b)=>a.name.localeCompare(b.name))){const child=path.posix.join(relative,entry.name);if(entry.isDirectory())result.push(...await walkFiles(root,child));else if(entry.isFile())result.push(child);}
  return result;
}

async function existingFile(root,relative){try{return(await stat(path.join(root,relative))).isFile();}catch{return false;}}

export async function resolveInputGroups(root,config,previousGraph=null,observedAt=new Date().toISOString()){
  const previous=new Map((previousGraph?.inputs??[]).map((item)=>[item.id,item]));const result=[];
  for(const group of config.groups){const members=[...group.files];for(const directory of group.roots)members.push(...await walkFiles(root,directory));members.sort();if(new Set(members).size!==members.length)throw new Error(`input ${group.id} memberが重複しています`);const currentDigest=await aggregateMemberDigest(root,members);const prior=previous.get(group.id);result.push({id:group.id,kind:group.kind,members,baseline_digest:prior?.baseline_digest??currentDigest,current_digest:currentDigest,observed_at:prior?.current_digest===currentDigest?prior.observed_at:observedAt});}
  return result;
}

export async function aggregateMemberDigest(root,members){
  const items=[];for(const relative of [...members].sort()){const bytes=await readFile(path.join(root,relative));items.push({path:relative,digest:sha256(bytes)});}return sha256(items);
}

export async function discoverPortalOutputs(root){
  const paths=new Set(['app/data/index.generated.json','app/data/index-bootstrap.generated.json','evals/router.skill-eval.json','evidence/import-report.json','evidence/non-regression-harness.json','evidence/non-regression-report.json','evidence/scenarios/closure-plan.json','evidence/scenarios/index.json','provenance.yaml','sbom.npm.spdx.json','sbom.spdx.json']);
  try{const bootstrap=JSON.parse(await readFile(path.join(root,'app/data/index-bootstrap.generated.json'),'utf8'));if(/^\/data\/index\/[a-f0-9]{64}\.json$/.test(bootstrap.publicUrl))paths.add(`public${bootstrap.publicUrl}`);}catch{}
  for(const directory of ['evidence/reports','evidence/scenarios'])for(const relative of await walkFiles(root,directory))if(/\.json$/.test(relative))paths.add(relative);
  for(const name of await readdir(path.join(root,'evidence')))if(/\.evidence\.json$/.test(name))paths.add(`evidence/${name}`);
  return[...paths].filter((relative)=>existingFile(root,relative)).sort();
}

function outputId(relative){return`output.${relative.toLowerCase().replace(/[^a-z0-9]+/g,'.').replace(/^\.|\.$/g,'')}`;}
function outputKind(relative){if(relative.endsWith('closure-plan.json'))return'closure-plan';if(relative.includes('/scenarios/'))return'scenario-proof';if(relative.includes('performance'))return'benchmark';if(relative.includes('router')||relative.includes('skill-eval'))return'skill-eval';if(relative.endsWith('.evidence.json')||relative==='provenance.yaml')return'derived-evidence';return'runtime-evidence';}

async function proofStructureDigest(root){
  const index=JSON.parse(await readFile(path.join(root,'evidence/scenarios/index.json'),'utf8'));const files=[];
  for(const item of index.files??[]){const proof=JSON.parse(await readFile(path.join(root,item.path),'utf8'));files.push({id:item.id,pattern_id:item.pattern_id,scenario:item.scenario,path:item.path,proof_id:proof.id,target_id:proof.target_id,target_set:proof.target_set,behavior_scope:proof.behavior_scope,source_bindings:(proof.source_bindings??[]).map((binding)=>({variant_id:binding.variant_id,path:binding.path}))});}
  return sha256({id:index.id,atlas_id:index.atlas_id,denominator:index.denominator,files});
}

async function closureStructureDigest(root){
  const plan=JSON.parse(await readFile(path.join(root,'evidence/scenarios/closure-plan.json'),'utf8'));const tranches=[];for(const field of ['completed_tranches','tranches'])for(const item of plan[field]??[])tranches.push({id:item.id,risk_rank:item.risk_rank,scenario:item.scenario,row_ids:item.row_ids,pattern_rows:item.pattern_rows,variant_runs:item.variant_runs,commit_policy:item.commit_policy});const ordered=[];for(const item of plan.completed_tranches??[])ordered.push(...(item.row_ids??[]));for(const item of plan.rows??[])ordered.push(item.id);return sha256({id:plan.id,scope:plan.scope,policy:plan.policy,baseline:plan.baseline,tranches,ordered_row_ids:ordered});
}

export async function buildPortalGraph(root,{inputs,startedAt,completedAt,runtimeIdentity}){
  const paths=await discoverPortalOutputs(root);const inputIds=inputs.map((item)=>item.id);const idByPath=new Map(paths.map((relative)=>[relative,outputId(relative)]));const evidenceWrappers=new Map();
  for(const relative of paths.filter((item)=>item.endsWith('.evidence.json'))){const record=JSON.parse(await readFile(path.join(root,relative),'utf8'));evidenceWrappers.set(relative,record.artifact.uri);}
  const outputs=[];
  for(const relative of paths){let dependsOn=inputIds;if(relative==='app/data/index-bootstrap.generated.json'||relative.startsWith('public/data/index/')){dependsOn=[idByPath.get('app/data/index.generated.json')];}else if(evidenceWrappers.has(relative)){const artifact=evidenceWrappers.get(relative);dependsOn=idByPath.has(artifact)?[idByPath.get(artifact),'portal-harness','portal-profile']:['portal-harness','portal-profile'];}else if(relative==='provenance.yaml'){dependsOn=[...paths.filter((item)=>item.endsWith('.evidence.json')).map((item)=>idByPath.get(item)),'portal-source','portal-harness','portal-runtime'];}outputs.push({id:idByPath.get(relative),kind:outputKind(relative),path:relative,digest:sha256(await readFile(path.join(root,relative))),depends_on:[...new Set(dependsOn)],status:'current',run_id:'portal-reproduce-run'});}
  const bindings=inputs.map((item)=>({input_id:item.id,digest:item.current_digest}));
  return{schema_version:1,atlas_id:'executable-technology-atlas',generated_at:completedAt,status:'current',policy:POLICY,inputs,outputs,runs:[{id:'portal-reproduce-run',execution_kind:'runtime',command:'npm run dependency:reproduce',started_at:startedAt,completed_at:completedAt,result:'passed',attempts:1,runtime_identity:runtimeIdentity,input_bindings:bindings,output_ids:outputs.map((item)=>item.id)}],required_outputs:outputs.map((item)=>item.path),structures:[{id:'portal-proof-topology-v1',kind:'scenario-proof-index',path:'evidence/scenarios/index.json',baseline_digest:await proofStructureDigest(root)},{id:'portal-closure-topology-v1',kind:'scenario-closure-plan',path:'evidence/scenarios/closure-plan.json',baseline_digest:await closureStructureDigest(root)}]};
}

export async function auditPortalGraph(root,graph,schema){
  const errors=[];const ajv=new Ajv2020({allErrors:true,strict:true});addFormats(ajv);const validate=ajv.compile(schema);if(!validate(graph))errors.push(`Schema: ${ajv.errorsText(validate.errors)}`);
  const inputIds=new Set((graph.inputs??[]).map((item)=>item.id));for(const input of graph.inputs??[]){let actual=null;try{actual=await aggregateMemberDigest(root,input.members);}catch(error){errors.push(`input ${input.id}: ${error.message}`);}if(actual&&actual!==input.current_digest)errors.push(`input ${input.id} current_digest不一致`);}
  const outputIds=new Set((graph.outputs??[]).map((item)=>item.id));const paths=new Set();for(const output of graph.outputs??[]){if(paths.has(output.path))errors.push(`output path重複: ${output.path}`);paths.add(output.path);let bytes=null;try{bytes=await readFile(path.join(root,output.path));}catch(error){errors.push(`output ${output.id}: ${error.message}`);}if(bytes&&sha256(bytes)!==output.digest)errors.push(`output ${output.id} digest不一致`);for(const dependency of output.depends_on??[])if(!inputIds.has(dependency)&&!outputIds.has(dependency))errors.push(`output ${output.id} unknown dependency: ${dependency}`);}
  const discovered=await discoverPortalOutputs(root);for(const relative of discovered)if(!paths.has(relative))errors.push(`required output欠落: ${relative}`);for(const relative of graph.required_outputs??[])if(!paths.has(relative))errors.push(`required_outputsの実体欠落: ${relative}`);
  const run=(graph.runs??[]).find((item)=>item.id==='portal-reproduce-run');const bindings=new Map((run?.input_bindings??[]).map((item)=>[item.input_id,item.digest]));for(const input of graph.inputs??[])if(bindings.get(input.id)!==input.current_digest)errors.push(`run binding不一致: ${input.id}`);for(const output of graph.outputs??[])if(!run?.output_ids?.includes(output.id))errors.push(`run output欠落: ${output.id}`);
  const expectedStructures=[await proofStructureDigest(root),await closureStructureDigest(root)];for(const[index,structure]of(graph.structures??[]).entries())if(expectedStructures[index]!==structure.baseline_digest)errors.push(`structure drift: ${structure.kind}`);
  return{ok:errors.length===0,errors,summary:{inputs:graph.inputs?.length??0,changedInputs:(graph.inputs??[]).filter((item)=>item.baseline_digest!==item.current_digest).length,outputs:graph.outputs?.length??0,runs:graph.runs?.length??0,requiredOutputs:graph.required_outputs?.length??0,structures:graph.structures?.length??0},canonicalDigest:sha256(Buffer.from(canonicalJson(graph)))};
}
