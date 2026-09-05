import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { auditPortalGraph, buildPortalGraph, discoverPortalOutputs, resolveInputGroups, validatePortalContentAddressedIndexMigration } from '../scripts/lib/portal-dependency-graph.mjs';

const root=process.cwd();
const config=JSON.parse(await readFile(path.join(root,'contracts/portal-evidence-dependency-inputs.json'),'utf8'));
const fixture=JSON.parse(await readFile(path.join(root,'fixtures/evidence-dependency/digest-only-closure.json'),'utf8'));
const migration=JSON.parse(await readFile(path.join(root,'contracts/portal-content-addressed-index-migration.json'),'utf8'));
const migrationSchema=JSON.parse(await readFile(path.join(root,'contracts/schemas/portal-content-addressed-index-migration.schema.json'),'utf8'));
const migrationNegative=JSON.parse(await readFile(path.join(root,'fixtures/evidence-dependency/content-addressed-index-migration-negative-cases.json'),'utf8'));
const proof=JSON.parse(await readFile(path.join(root,'evidence/scenarios/portal-dependency-current.proof.json'),'utf8'));
const dependencyGraphSchema=JSON.parse(await readFile(path.join(root,'contracts/schemas/evidence-dependency-graph.schema.json'),'utf8'));

function applyMigrationNegative(document,mutation){
  const mutated=structuredClone(document);
  const oldPath=mutated.replacements[0].from.path;
  const currentPath=mutated.current.path;
  if(mutation==='promote-old-as-current')mutated.current=structuredClone(mutated.replacements[0].from);
  else if(mutation==='drop-current-preserved')mutated.preservedPaths=mutated.preservedPaths.filter((item)=>item!==currentPath);
  else if(mutation==='allow-old-index-deletion')mutated.policy.allowOldIndexDeletion=true;
  else if(mutation==='allow-digest-only-rebinding')mutated.policy.digestOnlyRebinding=true;
  else if(mutation==='disable-graph-refresh-after-import')mutated.policy.graphRefreshAfterImport=false;
  else if(mutation==='shared-target')mutated.replacements.push(structuredClone(mutated.replacements[0]));
  else if(mutation==='drop-old-preserved')mutated.preservedPaths=mutated.preservedPaths.filter((item)=>item!==oldPath);
  else throw new Error(`未知のmigration負例です: ${mutation}`);
  return mutated;
}

function applyGraphNegative(graph,mutation){
  const mutated=structuredClone(graph);
  const oldPath=migration.replacements[0].from.path;
  const currentPath=migration.current.path;
  const oldOutput=mutated.outputs.find((item)=>item.path===oldPath);
  const currentOutput=mutated.outputs.find((item)=>item.path===currentPath);
  const run=mutated.runs.find((item)=>item.id==='portal-reproduce-run');
  if(mutation==='drop-current-required-output')mutated.required_outputs=mutated.required_outputs.filter((item)=>item!==currentPath);
  else if(mutation==='promote-historical-output')oldOutput.status='current';
  else if(mutation==='drop-current-run-output')run.output_ids=run.output_ids.filter((item)=>item!==currentOutput.id);
  else if(mutation==='add-historical-run-output')run.output_ids=[...run.output_ids,oldOutput.id];
  else throw new Error(`未知のgraph負例です: ${mutation}`);
  return mutated;
}

async function buildCurrentGraph(){
  const previousGraph=JSON.parse(await readFile(path.join(root,'evidence/dependency-graph.json'),'utf8'));
  const inputs=await resolveInputGroups(root,config,previousGraph,'2026-08-31T00:00:00.000Z');
  return buildPortalGraph(root,{inputs,startedAt:'2026-08-31T00:00:00.000Z',completedAt:'2026-08-31T00:00:01.000Z',runtimeIdentity:{node:'v25.2.1',npm:'11.6.2',os:'darwin-25.1.0-arm64',profile:'local'}});
}

test('Portal Graph入力はSource TreeやDefault BranchではなくRepository内の固定memberだけを列挙する',()=>{assert.equal(config.groups.length,4);assert.deepEqual(config.groups.map((item)=>item.kind),['source','harness','runtime','profile']);const serialized=JSON.stringify(config);assert.doesNotMatch(serialized,/default_branch|\.git\/|submodule/i);});
test('Portal自身のbounded Closureは97 Subjectのsubject-definitiveを0のまま分離する',()=>{assert.equal(proof.completion_boundary.portal_completion_class,'bounded-complete');assert.equal(proof.completion_boundary.subject_definitive_count,0);assert.equal(proof.completion_boundary.subject_auto_promotion,false);});
test('digest-only負例はSource変更後の未再実行outputをCore診断で拒否する契約を固定する',()=>{assert.equal(fixture.inputKind,'source');assert.equal(fixture.expectedExitCode,1);assert.match(fixture.expectedDiagnostic,/影響Evidenceがstaleのままです/);assert.match(fixture.expectedDiagnostic,/76090e9b725c469db2cfbe02a8c5f3ab8874b6422cba88d37bd7bec6e7aed3b0/);assert.ok(fixture.observedAfterRunSeconds>0);});
test('content-addressed index migration contractはappend-only historyとone-to-one replacementを固定する',async()=>{const result=await validatePortalContentAddressedIndexMigration(root,migration,migrationSchema);assert.equal(result.ok,true,result.errors.join('; '));assert.equal(migration.preservedPaths.length,2);assert.equal(migration.replacements.length,1);assert.equal(migration.policy.allowOldIndexDeletion,false);assert.equal(migration.policy.digestOnlyRebinding,false);});
test('recorded dependency graphはfull reproduce後currentで、入力digest再束縛をfail-closedする',async()=>{const graph=JSON.parse(await readFile(path.join(root,'evidence/dependency-graph.json'),'utf8'));const current=await auditPortalGraph(root,graph,dependencyGraphSchema);assert.equal(current.ok,true,current.errors.join('; '));assert.deepEqual(current.summary,{inputs:4,changedInputs:4,outputs:39,runs:1,requiredOutputs:39,structures:2});const rebound=structuredClone(graph);rebound.inputs.find((item)=>item.id==='portal-harness').current_digest='sha256:0000000000000000000000000000000000000000000000000000000000000000';const stale=await auditPortalGraph(root,rebound,dependencyGraphSchema);assert.equal(stale.ok,false,'recorded input digest rebinding must not be treated as current');assert.ok(stale.errors.includes('input portal-harness current_digest不一致'));assert.ok(stale.errors.includes('run binding不一致: portal-harness'));});
test('current output discoveryとsynthetic graphは新旧content-addressed indexを正しいstatusで保持する',async()=>{const discovered=await discoverPortalOutputs(root);assert.equal(discovered.length,39);for(const required of ['public/data/index/76090e9b725c469db2cfbe02a8c5f3ab8874b6422cba88d37bd7bec6e7aed3b0.json','public/data/index/25c8ba3c8b0560f1a99f992e097c853d0a594849fda2ad445768ee060583332f.json','evidence/portal-ci-checkpoint-readiness.json','evidence/portal-distribution-gap-index.json','evidence/portal-distribution-input-bindings.json','evidence/portal-distribution-readiness.json','evidence/portal-distribution-verification-matrix.json','evidence/portal-import-lifecycle-visibility.json','evidence/portal-root-artifact-gap-index.json','evidence/portal-root-definitive-certificate-readiness.json','evidence/portal-root-definitive-declaration-readiness.json','evidence/portal-root-depth-parity-readiness.json','evidence/portal-root-migration-readiness.json','evidence/portal-root-surface-inventory-readiness.json','evidence/portal-root-verification-matrix-readiness.json'])assert.ok(discovered.includes(required),required);const graph=await buildCurrentGraph();const oldOutput=graph.outputs.find((item)=>item.path===migration.replacements[0].from.path);const currentOutput=graph.outputs.find((item)=>item.path===migration.current.path);const run=graph.runs.find((item)=>item.id==='portal-reproduce-run');assert.equal(oldOutput.status,'stale');assert.equal(currentOutput.status,'current');assert.equal(run.output_ids.includes(oldOutput.id),false);assert.equal(run.output_ids.includes(currentOutput.id),true);const result=await auditPortalGraph(root,graph,dependencyGraphSchema);assert.equal(result.ok,true,result.errors.join('; '));});
test('migrationとgraphのnegativeはdeletion・shared replacement・wrong order・digest-only rebindingを拒否する',async()=>{assert.equal(migrationNegative.migrationCases.length,7);for(const item of migrationNegative.migrationCases){const result=await validatePortalContentAddressedIndexMigration(root,applyMigrationNegative(migration,item.mutation),migrationSchema);assert.equal(result.ok,false,item.caseId);assert.ok(result.errors.includes(item.expectedDiagnostic),`${item.caseId}: ${result.errors.join('; ')}`);}const graph=await buildCurrentGraph();assert.equal(migrationNegative.graphCases.length,4);for(const item of migrationNegative.graphCases){const result=await auditPortalGraph(root,applyGraphNegative(graph,item.mutation),dependencyGraphSchema);assert.equal(result.ok,false,item.caseId);assert.ok(result.errors.includes(item.expectedDiagnostic),`${item.caseId}: ${result.errors.join('; ')}`);}});
