import assert from 'node:assert/strict';
import test from 'node:test';
import { GET, dynamic, revalidate } from '../app/api/integration-status/route.js';
import { isPortalIntegrationStatusSnapshot } from '../app/lib/portal-integration-status.mjs';
import { evaluatePortalIntegrationStatus } from '../scripts/lib/portal-integration-status.mjs';

test('integration-status APIはsame-origin read-only reportをno-storeで返す',async()=>{
  assert.equal(dynamic,'force-dynamic');
  assert.equal(revalidate,0);
  const expected=await evaluatePortalIntegrationStatus(process.cwd());
  const response=await GET();
  assert.equal(response.status,200);
  assert.equal(response.headers.get('cache-control'),'no-store');
  assert.equal(response.headers.get('content-type'),'application/json; charset=utf-8');
  const report=await response.json();
  assert.equal(isPortalIntegrationStatusSnapshot(report),true);
  assert.equal(report.status,expected.report.status);
  assert.equal(report.distribution.subjects,97);
  assert.equal(report.distribution.ready,0);
  assert.equal(report.root.artifactsMissing,5);
  assert.equal(report.root.coreMatrixArtifactStatus,'present');
  assert.equal(report.root.matrixGap,478);
  assert.deepEqual(report.evidenceRefresh,expected.report.evidenceRefresh);
  assert.equal(report.boundary.completionEffect,'none');
});
