import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { sha256 } from '../scripts/lib/crypto.mjs';
import { missingEvidenceDependency, projectEvidenceDependency, validateEvidenceDependencyEnvelope } from '../scripts/lib/evidence-dependency.mjs';

const root=process.cwd();
const lockBytes=await readFile(path.join(root,'contracts/evidence-dependency-lock.json'));
const lock=JSON.parse(lockBytes);
const schemaBytes=await readFile(path.join(root,'contracts/schemas/evidence-dependency-graph.schema.json'));
const schema=JSON.parse(schemaBytes);
const contractDocumentBytes=await readFile(path.join(root,lock.vendoredContractDocumentPath));
const digest=(value)=>`sha256:${value.repeat(64).slice(0,64)}`;

function fixture({changed=false,gateResult='pass',executionKind='derived'}={}){
  const graph={schema_version:1,atlas_id:'example-atlas',generated_at:'2026-08-29T00:00:00Z',status:gateResult==='pass'?'current':'stale',policy:{transitive_staleness:true,digest_only_closure_forbidden:true,actual_rerun_required:true,missing_rerun_targets_fail:true,proof_structure_invariant:true,closure_plan_structure_invariant:true},inputs:[{id:'source',kind:'source',members:['src/a.ts'],baseline_digest:digest('a'),current_digest:changed?digest('b'):digest('a'),observed_at:'2026-08-29T00:00:00Z'}],outputs:[{id:'proof',kind:'scenario-proof',path:'evidence/proof.json',digest:digest('c'),depends_on:['source'],status:gateResult==='pass'?'current':'stale',run_id:'run'}],runs:[{id:'run',execution_kind:executionKind,command:'npm test',started_at:'2026-08-29T00:00:00Z',completed_at:'2026-08-29T00:01:00Z',result:'passed',attempts:1,...(executionKind==='derived'?{}:{runtime_identity:{node:'22.22.0',os:'ubuntu-24.04'}}),input_bindings:[{input_id:'source',digest:changed?digest('b'):digest('a')}],output_ids:['proof']}],required_outputs:['evidence/proof.json'],structures:[{id:'scenario-proof-index',kind:'scenario-proof-index',path:'evidence/proof.json',baseline_digest:digest('d')},{id:'scenario-closure-plan',kind:'scenario-closure-plan',path:'evidence/closure.json',baseline_digest:digest('e')}]};
  const graphDigest=sha256(graph);
  const coreGate={schemaVersion:1,coreCommit:lock.coreCommit,command:'atlas audit . --gate evidence-dependency',result:gateResult,executedAt:'2026-08-29T00:02:00Z',runtimeIdentity:{node:'22.22.0',os:'ubuntu-24.04'},graphDigest,missingRequiredOutputs:[],structureResults:[{id:'scenario-proof-index',status:'current',detail:'shape current'},{id:'scenario-closure-plan',status:'current',detail:'shape current'}],diagnostics:gateResult==='pass'?[]:['input changed; actual rerun required']};
  const payload={subjectId:'example-subject',atlasId:'example-atlas',repository:'example-atlas',sourceCommit:'0123456789abcdef0123456789abcdef01234567',coreCommit:lock.coreCommit,graphPath:'evidence/dependency-graph.json',graphDigest,graph,coreGate};
  return{kind:'portal-evidence-dependency',release:{digest:sha256(payload)},payload};
}

test('Schema・契約文書と正式Core main/CI成功commitをbytes固定する',()=>{assert.equal(sha256(schemaBytes),lock.schemaDigest);assert.equal(sha256(contractDocumentBytes),lock.contractDocumentDigest);assert.equal(lock.coreRef,'main');assert.equal(lock.coreCommit,'072d7ca77981f51754e824d70c6d4ecd55ea67e5');assert.equal(lock.coreCommitStatus,'official-main-ci-passed');assert.equal(lock.gateAuthority,'core-gate-result-only');});
test('Graph欠落はrequired output missingで自動昇格しない',()=>{const value=missingEvidenceDependency({id:'missing-subject'});assert.equal(value.status,'missing-required-output');assert.equal(value.coreGate.result,'not-run');assert.equal(value.autoPromotion,false);assert.deepEqual(value.missingRequiredOutputs,['evidence/dependency-graph.json']);});
test('Core Gate passだけをcurrentとして投影する',()=>{const envelope=fixture();const validated=validateEvidenceDependencyEnvelope(envelope,lock,schema,{errors:[],trust:{usage:'fixture-only'}});assert.equal(validated.ok,true,validated.errors.join('; '));const projected=projectEvidenceDependency(envelope,validated,{trust:{usage:'fixture-only'}});assert.equal(projected.status,'current');assert.equal(projected.outputs[0].run.command,'npm test');assert.equal(projected.summary.structureDrift,0);});
test('digest変更だけでは復旧済みにせず影響outputとstaleを保持する',()=>{const envelope=fixture({changed:true,gateResult:'fail'});const validated=validateEvidenceDependencyEnvelope(envelope,lock,schema,{errors:[],trust:{usage:'fixture-only'}});assert.equal(validated.ok,true,validated.errors.join('; '));const projected=projectEvidenceDependency(envelope,validated,{trust:{usage:'fixture-only'}});assert.equal(projected.status,'stale-or-incomplete');assert.equal(projected.inputs[0].state,'changed');assert.deepEqual(projected.outputs[0].impacted_by,['source']);});
test('runtime runのidentity欠落またはGate passのstructure driftを拒否する',()=>{const missingRuntime=fixture({executionKind:'runtime'});delete missingRuntime.payload.graph.runs[0].runtime_identity;missingRuntime.payload.graphDigest=sha256(missingRuntime.payload.graph);missingRuntime.payload.coreGate.graphDigest=missingRuntime.payload.graphDigest;assert.equal(validateEvidenceDependencyEnvelope(missingRuntime,lock,schema,{errors:[]}).ok,false);const drift=fixture();drift.payload.coreGate.structureResults[0].status='drift';assert.equal(validateEvidenceDependencyEnvelope(drift,lock,schema,{errors:[]}).ok,false);});
