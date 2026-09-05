import assert from 'node:assert/strict';
import test from 'node:test';
import { GET, dynamic, revalidate } from '../app/api/root-readiness-status/route.js';
import { isPortalRootReadinessStatusSnapshot } from '../app/lib/portal-root-readiness-status.mjs';

test('root-readiness-status APIはsame-origin read-only reportをno-storeで返す', async () => {
  assert.equal(dynamic, 'force-dynamic');
  assert.equal(revalidate, 0);
  const response = await GET();
  assert.equal(response.status, 200);
  assert.equal(response.headers.get('cache-control'), 'no-store');
  assert.equal(response.headers.get('content-type'), 'application/json; charset=utf-8');
  const report = await response.json();
  assert.equal(isPortalRootReadinessStatusSnapshot(report), true);
  assert.equal(report.root.missingArtifacts, 5);
  assert.equal(report.artifacts.length, 6);
  assert.equal(report.artifacts[2].artifactPath, 'verification.matrix.yaml');
  assert.equal(report.artifacts[2].observedStatus, 'present');
  assert.equal(report.boundary.completionEffect, 'none');
});
