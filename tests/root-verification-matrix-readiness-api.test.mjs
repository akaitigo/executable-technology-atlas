import assert from 'node:assert/strict';
import test from 'node:test';
import { GET, dynamic, revalidate } from '../app/api/root-verification-matrix-readiness/route.js';
import { isPortalRootVerificationMatrixReadinessSnapshot } from '../app/lib/portal-root-verification-matrix-readiness.mjs';

test('root-verification-matrix-readiness APIはsame-origin read-only reportをno-storeで返す', async () => {
  assert.equal(dynamic, 'force-dynamic');
  assert.equal(revalidate, 0);
  const response = await GET();
  assert.equal(response.status, 200);
  assert.equal(response.headers.get('cache-control'), 'no-store');
  assert.equal(response.headers.get('content-type'), 'application/json; charset=utf-8');
  const report = await response.json();
  assert.equal(isPortalRootVerificationMatrixReadinessSnapshot(report), true);
  assert.equal(report.summary.satisfied, 3);
  assert.equal(report.summary.blocked, 5);
  assert.equal(report.observed.portalDistributionMatrix.cells, 970);
  assert.equal(report.observed.portalDistributionMatrix.gap, 478);
  assert.equal(report.observed.portalDistributionMatrix.notEvaluated, 291);
  assert.equal(report.boundary.coreSubjectArtifact.path, 'verification.matrix.yaml');
  assert.equal(report.boundary.coreSubjectArtifact.status, 'present');
  assert.equal(report.boundary.completionEffect, 'none');
});

test('browser guardはGraph bindingの分母・差分・一意性をfail-closedで検証する', async () => {
  const response = await GET();
  assert.equal(response.status, 200);
  const report = await response.json();

  const invalidCount = structuredClone(report);
  invalidCount.observed.dependencyGraph.boundRequiredOutputs += 1;
  assert.equal(isPortalRootVerificationMatrixReadinessSnapshot(invalidCount), false);

  const duplicateMissing = structuredClone(report);
  duplicateMissing.observed.dependencyGraph.boundRequiredOutputs = 9;
  duplicateMissing.observed.dependencyGraph.missingRequiredOutputs = Array(2).fill(
    'evidence/portal-distribution-gap-index.json',
  );
  assert.equal(isPortalRootVerificationMatrixReadinessSnapshot(duplicateMissing), false);

  const unknownMissing = structuredClone(report);
  unknownMissing.observed.dependencyGraph.boundRequiredOutputs = 10;
  unknownMissing.observed.dependencyGraph.missingRequiredOutputs = ['evidence/not-a-required-output.json'];
  assert.equal(isPortalRootVerificationMatrixReadinessSnapshot(unknownMissing), false);
});
