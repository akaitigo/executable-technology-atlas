import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { aggregateMemberDigest, auditPortalGraph, discoverPortalOutputs } from './portal-dependency-graph.mjs';
import { canonicalJson, sha256 } from './crypto.mjs';

const POLICY_PATH='contracts/portal-evidence-refresh-policy.json';
const SCHEMA_PATH='contracts/schemas/portal-evidence-refresh-policy.schema.json';
const PACKAGE_PATH='package.json';
const EXPECTED_WRAPPERS=[
  'evidence/dependency.own-closure.evidence.json',
  'evidence/import.integrity.evidence.json',
  'evidence/non-regression.evidence.json',
  'evidence/performance.budget.evidence.json',
  'evidence/publication.sbom.evidence.json',
  'evidence/router.eval.evidence.json',
  'evidence/security.headers.evidence.json',
  'evidence/ui.build.evidence.json'
];
const EXPECTED_STAGES=[
  {id:'import',script:'node scripts/import-releases.mjs'},
  {id:'non-regression',script:'node scripts/check-non-regression.mjs'},
  {id:'eval',script:'node scripts/run-evals.mjs'},
  {id:'sbom',script:'node scripts/generate-sbom.mjs'},
  {id:'build',script:'vinext build'},
  {id:'perf',script:'node scripts/performance-budget.mjs'},
  {id:'evidence',script:'node scripts/refresh-evidence.mjs'},
  {id:'provenance',script:'node scripts/generate-provenance.mjs'}
];

export async function loadPortalEvidenceRefreshPolicy(root=process.cwd()){
  const [policyBytes,schemaBytes]=await Promise.all([readFile(path.join(root,POLICY_PATH)),readFile(path.join(root,SCHEMA_PATH))]);
  return{policy:JSON.parse(policyBytes),schema:JSON.parse(schemaBytes),policyBytes,schemaBytes};
}

export function validatePortalEvidenceRefreshPolicy(policy,schema){
  const errors=[];const ajv=new Ajv2020({allErrors:true,strict:true});addFormats(ajv);const validate=ajv.compile(schema);if(!validate(policy))errors.push('schema-invalid');
  if(canonicalJson(policy.requiredWrappers)!==canonicalJson(EXPECTED_WRAPPERS))errors.push('refresh-wrapper-denominator-reduced-or-reordered');
  if(canonicalJson(policy.pipeline?.stages)!==canonicalJson(EXPECTED_STAGES))errors.push('refresh-stage-denominator-reduced-or-reordered');
  if(policy.pipeline?.command!=='npm run dependency:reproduce'||policy.pipeline?.entrypoint!=='node scripts/refresh-portal-dependency-graph.mjs --record')errors.push('refresh-pipeline-rebound');
  const boundary=policy.boundary??{};
  if(boundary.readOnly!==true||boundary.autoRun!==false||boundary.digestOnlyClosure!==false||boundary.wrapperRewriteIsRerun!==false||boundary.stageSkipAllowed!==false||boundary.runtimeSubstitution!==false||boundary.recordedGraphStatusIsCurrentProof!==false||boundary.completionEffect!=='none')errors.push('refresh-boundary-weakened');
  return{ok:errors.length===0,errors:[...new Set(errors)]};
}

async function inspectWrapper(root,relative){
  try{
    const wrapperBytes=await readFile(path.join(root,relative));const wrapper=JSON.parse(wrapperBytes);const uri=wrapper.artifact?.uri??'';
    if(!uri||path.isAbsolute(uri)||uri.split('/').includes('..'))return{path:relative,id:wrapper.id??null,artifactPath:uri,state:'stale',digestMatch:false,sizeMatch:false,error:'wrapper-artifact-path-invalid'};
    const artifactBytes=await readFile(path.join(root,uri));const digestMatch=sha256(artifactBytes)===wrapper.artifact?.digest;const sizeMatch=artifactBytes.length===wrapper.artifact?.size_bytes;
    return{path:relative,id:wrapper.id,artifactPath:uri,state:digestMatch&&sizeMatch?'current':'stale',digestMatch,sizeMatch,error:null};
  }catch(error){return{path:relative,id:null,artifactPath:null,state:'stale',digestMatch:false,sizeMatch:false,error:error.message};}
}

export async function evaluatePortalEvidenceRefreshReadiness(root,policy,schema){
  const policyResult=validatePortalEvidenceRefreshPolicy(policy,schema);const errors=[...policyResult.errors];

  const [packageBytes,graphBytes,graphSchemaBytes]=await Promise.all([readFile(path.join(root,PACKAGE_PATH)),readFile(path.join(root,policy.graphPath)),readFile(path.join(root,policy.graphSchemaPath))]);
  const packageDocument=JSON.parse(packageBytes);const graph=JSON.parse(graphBytes);const graphSchema=JSON.parse(graphSchemaBytes);
  if(packageDocument.scripts?.['dependency:reproduce']!==policy.pipeline.entrypoint||policy.pipeline.stages.some((stage)=>packageDocument.scripts?.[stage.id]!==stage.script))errors.push('refresh-package-entrypoint-drift');
  const wrappers=await Promise.all(EXPECTED_WRAPPERS.map((relative)=>inspectWrapper(root,relative)));
  const staleWrappers=wrappers.filter((item)=>item.state==='stale');
  const inputStates=[];
  for(const input of graph.inputs??[]){let actualDigest=null;try{actualDigest=await aggregateMemberDigest(root,input.members);}catch{}inputStates.push({id:input.id,recordedDigest:input.current_digest,actualDigest,current:actualDigest===input.current_digest});}
  const changedInputs=inputStates.filter((item)=>!item.current);
  const discovered=await discoverPortalOutputs(root);const recordedPaths=new Set((graph.outputs??[]).map((item)=>item.path));const missingOutputs=discovered.filter((relative)=>!recordedPaths.has(relative));
  const graphAudit=await auditPortalGraph(root,graph,graphSchema);const run=(graph.runs??[]).find((item)=>item.command===policy.pipeline.command);const runtimeIdentityPresent=run?.result==='passed'&&Object.keys(run.runtime_identity??{}).length>0;
  const currentRerun=graphAudit.ok&&staleWrappers.length===0&&changedInputs.length===0&&missingOutputs.length===0&&runtimeIdentityPresent;
  const state=(condition)=>condition?'satisfied':'blocked';
  const prerequisites=[
    {id:'fixed-reproduction-pipeline',state:state(!errors.includes('refresh-pipeline-rebound')&&!errors.includes('refresh-stage-denominator-reduced-or-reordered')&&!errors.includes('refresh-package-entrypoint-drift'))},
    {id:'recorded-runtime-identity',state:state(runtimeIdentityPresent)},
    {id:'current-input-bindings',state:state(changedInputs.length===0)},
    {id:'evidence-wrapper-freshness',state:state(staleWrappers.length===0)},
    {id:'discovered-output-coverage',state:state(missingOutputs.length===0)},
    {id:'actual-current-rerun',state:state(currentRerun)}
  ];
  const satisfied=prerequisites.filter((item)=>item.state==='satisfied').length;
  const report={schemaVersion:1,id:'portal-evidence-refresh-readiness',status:currentRerun?'ready':'blocked',classification:'dynamic-read-only-readiness',source:{policy:{path:POLICY_PATH,digest:sha256(Buffer.from(`${JSON.stringify(policy,null,2)}\n`))},package:{path:PACKAGE_PATH,digest:sha256(packageBytes)},graph:{path:policy.graphPath,digest:sha256(graphBytes)}},summary:{prerequisites:prerequisites.length,satisfied,blocked:prerequisites.length-satisfied,wrappers:wrappers.length,currentWrappers:wrappers.length-staleWrappers.length,staleWrappers:staleWrappers.length,inputs:inputStates.length,inputsChangedSinceRun:changedInputs.length,recordedOutputs:graph.outputs?.length??0,discoveredOutputs:discovered.length,missingDiscoveredOutputs:missingOutputs.length,graphCurrent:graphAudit.ok,currentRerun,completionEffect:'none'},prerequisites,wrappers,inputs:inputStates,missingOutputs,lastRecordedRun:run?{command:run.command,result:run.result,startedAt:run.started_at,completedAt:run.completed_at,runtimeIdentity:run.runtime_identity}:null,pipeline:policy.pipeline,boundary:{...policy.boundary,subjectDefinitiveEffect:'none',distributionEffect:'none',rootDefinitiveEffect:'none'}};
  return{ok:errors.length===0,errors:[...new Set(errors)],report};
}

export function applyPortalEvidenceRefreshPolicyNegative(policy,testCase){
  const mutated=structuredClone(policy);
  if(testCase.mutation==='remove-stage')mutated.pipeline.stages.pop();
  else if(testCase.mutation==='remove-wrapper')mutated.requiredWrappers.pop();
  else if(testCase.mutation==='rebind-command')mutated.pipeline.command='npm run gate';
  else if(testCase.mutation==='rebind-entrypoint')mutated.pipeline.entrypoint='node scripts/refresh-evidence.mjs';
  else if(testCase.mutation==='allow-digest-only')mutated.boundary.digestOnlyClosure=true;
  else if(testCase.mutation==='promote-wrapper-rewrite')mutated.boundary.wrapperRewriteIsRerun=true;
  else if(testCase.mutation==='allow-stage-skip')mutated.boundary.stageSkipAllowed=true;
  else if(testCase.mutation==='allow-runtime-substitution')mutated.boundary.runtimeSubstitution=true;
  else if(testCase.mutation==='promote-recorded-status')mutated.boundary.recordedGraphStatusIsCurrentProof=true;
  else throw new Error(`未知のEvidence refresh負例です: ${testCase.mutation}`);
  return mutated;
}
