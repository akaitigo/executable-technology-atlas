import assert from 'node:assert/strict';
import test from 'node:test';
import { GET, dynamic, revalidate } from '../app/api/evidence-status/route.js';
import { isPortalEvidenceRefreshStatusSnapshot } from '../app/lib/portal-evidence-refresh-status.mjs';
import { evaluatePortalEvidenceRefreshReadiness, loadPortalEvidenceRefreshPolicy } from '../scripts/lib/portal-evidence-refresh-readiness.mjs';

test('evidence-status APIはsame-origin read-only reportをno-storeで返す', async () => {
  assert.equal(dynamic, 'force-dynamic');
  assert.equal(revalidate, 0);
  const { policy, schema } = await loadPortalEvidenceRefreshPolicy(process.cwd());
  const expected = (await evaluatePortalEvidenceRefreshReadiness(process.cwd(), policy, schema)).report;
  const response = await GET();
  assert.equal(response.status, 200);
  assert.equal(response.headers.get('cache-control'), 'no-store');
  assert.equal(response.headers.get('content-type'), 'application/json; charset=utf-8');
  const report = await response.json();
  assert.equal(isPortalEvidenceRefreshStatusSnapshot(report), true);
  assert.equal(report.status, expected.status);
  assert.equal(report.summary.wrappers, 8);
  assert.equal(report.summary.currentWrappers + report.summary.staleWrappers, 8);
  assert.equal(report.summary.staleWrappers, expected.summary.staleWrappers);
  assert.equal(report.summary.inputsChangedSinceRun, expected.summary.inputsChangedSinceRun);
  assert.equal(report.summary.missingDiscoveredOutputs, expected.summary.missingDiscoveredOutputs);
  assert.equal(report.summary.currentRerun, expected.summary.currentRerun);
  assert.equal(report.boundary.completionEffect, 'none');
});
