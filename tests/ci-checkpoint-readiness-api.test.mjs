import assert from 'node:assert/strict';
import test from 'node:test';
import { GET, dynamic, revalidate } from '../app/api/ci-checkpoint-readiness/route.js';
import { isPortalCiCheckpointReadinessSnapshot } from '../app/lib/portal-ci-checkpoint-readiness.mjs';

test('ci-checkpoint-readiness APIはsame-origin read-only reportをno-storeで返す', async () => {
  assert.equal(dynamic, 'force-dynamic');
  assert.equal(revalidate, 0);
  const response = await GET();
  assert.equal(response.status, 200);
  assert.equal(response.headers.get('cache-control'), 'no-store');
  assert.equal(response.headers.get('content-type'), 'application/json; charset=utf-8');
  const report = await response.json();
  assert.equal(isPortalCiCheckpointReadinessSnapshot(report), true);
  assert.equal(report.status, 'blocked');
  assert.equal(report.summary.prerequisites, 9);
  assert.equal(report.summary.satisfied, 3);
  assert.equal(report.summary.blocked, 6);
  assert.equal(report.observed.subjectAggregation.subjectDefinitive, 0);
  assert.equal(report.observed.root.missingArtifacts, 5);
  assert.equal(report.observed.ci.sameShaVerified, false);
  assert.equal(report.boundary.completionEffect, 'none');
});
