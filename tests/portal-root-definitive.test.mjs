import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';

const root=process.cwd();
const lock=JSON.parse(await readFile(path.join(root,'contracts/portal-root-definitive-lock.json'),'utf8'));
const report=JSON.parse(await readFile(path.join(root,'evidence/portal-root-definitive-report.json'),'utf8'));

test('Portal root Definitive実監査失敗をbounded Certificateや配布Closureへ読み替えない',()=>{
  assert.equal(report.core.commit,lock.coreCommit);assert.equal(report.result,'fail');assert.equal(report.exitCode,1);assert.equal(report.status,'root-definitive-incomplete');assert.equal(report.completionClass,'not-definitive');assert.deepEqual(report.knownMissingArtifacts,lock.knownMissingArtifacts);assert.equal(report.failureOrdering,'core-order-independent');assert.equal(report.diagnosticClass,'known-required-root-artifact-unreadable');assert.deepEqual(report.boundary,{portalBoundedCertificate:'preserved-v1-local-evidence',subjectDefinitiveEffect:'none',distributionStatus:'not-established',distributionGapEffect:'none',completionEffect:'none',autoPromotion:false});
});

test('Portal root Definitive lockは正式Coreと実commandを固定する',()=>{
  assert.equal(lock.coreCommit,'072d7ca77981f51754e824d70c6d4ecd55ea67e5');assert.equal(lock.command,'atlas audit <portal-root> --gate definitive');assert.equal(lock.expectedExitCode,1);assert.equal(lock.expectedDiagnosticSuffix,'を読み込めません');assert.equal(lock.failureOrdering,'core-order-independent');assert.equal(lock.knownMissingArtifacts.length,6);
});
