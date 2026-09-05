import assert from 'node:assert/strict';
import test from 'node:test';
import { GET, dynamic, revalidate } from '../app/api/import-lifecycle/route.js';
import { isPortalImportLifecycleSnapshot } from '../app/lib/portal-import-lifecycle-visibility.mjs';

test('import-lifecycle APIはsame-origin read-only reportをno-storeで返す',async()=>{
  assert.equal(dynamic,'force-dynamic');
  assert.equal(revalidate,0);
  const response=await GET();
  assert.equal(response.status,200);
  assert.equal(response.headers.get('cache-control'),'no-store');
  assert.equal(response.headers.get('content-type'),'application/json; charset=utf-8');
  const report=await response.json();
  assert.equal(isPortalImportLifecycleSnapshot(report),true);
  assert.equal(report.status,'incomplete');
  assert.equal(report.actual.subjects,97);
  assert.equal(report.actual.verified,7);
  assert.equal(report.actual.absent,90);
  assert.equal(report.fixtureCoverage.staleLockCases,1);
  assert.equal(report.boundary.completionEffect,'none');
});
