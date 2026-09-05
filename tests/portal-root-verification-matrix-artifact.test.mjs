import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { applyPortalRootVerificationMatrixNegative, buildExpectedPortalRootVerificationMatrix, loadPortalRootVerificationMatrix, validatePortalRootVerificationMatrix } from '../scripts/lib/portal-root-verification-matrix.mjs';

const root = process.cwd();
const negative = JSON.parse(await readFile(path.join(root, 'fixtures/portal-root-verification-matrix/negative-cases.json'), 'utf8'));

test('Portal root verification matrixはactual Portal evidenceだけへ結び付いた10 rowを保持する', async () => {
  const loaded = await loadPortalRootVerificationMatrix(root);
  const result = await validatePortalRootVerificationMatrix(root, loaded.document);
  assert.equal(result.ok, true, result.errors.join(', '));
  assert.deepEqual(loaded.document, buildExpectedPortalRootVerificationMatrix());
  assert.deepEqual(result.summary, {
    rows: 10,
    requiredRows: 10,
    runtimeRows: 8,
    platformRows: 1,
    staticAllowedRows: 1,
    scenarios: ['normal', 'boundary', 'refusal', 'failure', 'recovery', 'migration', 'operations', 'security', 'performance', 'compatibility'],
    digest: null,
  });
});

test('Portal root verification matrixはrow削除・evidence drift・Subject化を拒否する', async () => {
  const loaded = await loadPortalRootVerificationMatrix(root);
  assert.equal(negative.cases.length, 4);
  for (const item of negative.cases) {
    const result = await validatePortalRootVerificationMatrix(root, applyPortalRootVerificationMatrixNegative(loaded.document, item));
    assert.equal(result.ok, false, item.caseId);
    assert.ok(result.errors.includes(item.expectedDiagnostic), `${item.caseId}: ${result.errors.join(', ')}`);
  }
});
