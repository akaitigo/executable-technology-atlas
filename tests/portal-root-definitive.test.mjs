import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { applyPortalRootSurfaceNegative, validatePortalRootSurfaceInventory } from '../scripts/lib/portal-root-surface-inventory.mjs';

const root=process.cwd();
const lock=JSON.parse(await readFile(path.join(root,'contracts/portal-root-definitive-lock.json'),'utf8'));
const report=JSON.parse(await readFile(path.join(root,'evidence/portal-root-definitive-report.json'),'utf8'));
const surfaceInventory=JSON.parse(await readFile(path.join(root,lock.portalInfrastructureSurfaceInventory.path),'utf8'));

test('Portal root Definitive実監査失敗をbounded Certificateや配布Closureへ読み替えない',()=>{
  assert.equal(report.core.commit,lock.coreCommit);assert.equal(report.result,'fail');assert.equal(report.exitCode,1);assert.equal(report.status,'root-definitive-incomplete');assert.equal(report.completionClass,'not-definitive');assert.deepEqual(report.knownMissingArtifacts,lock.knownMissingArtifacts);assert.equal(report.failureOrdering,'core-order-independent');assert.equal(report.diagnosticClass,'known-required-root-artifact-unreadable');assert.equal(report.portalInfrastructureArtifacts.length,1);assert.deepEqual(report.portalInfrastructureArtifacts[0].denominator,{masterySurfaces:14,coverageTargets:14,sourcePolicy:'portal-v1-authored-contracts'});assert.equal(report.portalInfrastructureArtifacts[0].inventedEdges,0);assert.deepEqual(report.boundary,{portalBoundedCertificate:'preserved-v1-local-evidence',subjectDefinitiveEffect:'none',distributionStatus:'not-established',distributionGapEffect:'none',completionEffect:'none',autoPromotion:false});
});

test('Portal root Definitive lockは正式Coreと実commandを固定する',()=>{
  assert.equal(lock.coreCommit,'072d7ca77981f51754e824d70c6d4ecd55ea67e5');assert.equal(lock.command,'atlas audit <portal-root> --gate definitive');assert.equal(lock.expectedExitCode,1);assert.equal(lock.expectedDiagnosticSuffix,'を読み込めません');assert.equal(lock.failureOrdering,'core-order-independent');assert.equal(lock.knownMissingArtifacts.length,6);assert.equal(lock.portalInfrastructureSurfaceInventory.expectedMasterySurfaceIds.length,14);assert.equal(lock.portalInfrastructureSurfaceInventory.expectedCoverageTargetIds.length,14);
});

test('Portal固有Surface Inventoryは実Mastery/Target分母を縮小せず保持する',async()=>{
  const result=await validatePortalRootSurfaceInventory(root,surfaceInventory,lock);
  assert.equal(result.ok,true,result.errors.join(', '));assert.deepEqual(result.summary,{masterySurfaces:14,coverageTargets:14,inventedEdges:0});
  assert.equal(surfaceInventory.mapping.status,'not-declared-in-v1-contract');assert.equal(surfaceInventory.boundary.coreSubjectArtifactStatus,'missing');assert.equal(surfaceInventory.boundary.subjectDefinitiveEffect,'none');assert.equal(surfaceInventory.boundary.completionEffect,'none');assert.equal(surfaceInventory.boundary.autoPromotion,false);
});

test('Portal固有Surface Inventoryの分母縮小・edge捏造・完成格上げを拒否する',async()=>{
  const fixture=JSON.parse(await readFile(path.join(root,'fixtures/portal-root-surface-inventory/negative-cases.json'),'utf8'));
  assert.equal(fixture.cases.length,4);
  for(const item of fixture.cases){const result=await validatePortalRootSurfaceInventory(root,applyPortalRootSurfaceNegative(surfaceInventory,item),lock);assert.equal(result.ok,false,item.caseId);assert.ok(result.errors.includes(item.expectedDiagnostic),`${item.caseId}: ${result.errors.join(', ')}`);}
});
