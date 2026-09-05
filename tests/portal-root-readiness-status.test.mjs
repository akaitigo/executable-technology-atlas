import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { assertPortalRootReadinessStatusSnapshot, isPortalRootReadinessStatusSnapshot } from '../app/lib/portal-root-readiness-status.mjs';
import { applyPortalRootReadinessStatusNegative, evaluatePortalRootReadinessStatus, validatePortalRootReadinessStatus } from '../scripts/lib/portal-root-readiness-status.mjs';

const root = process.cwd();
const negative = JSON.parse(await readFile(path.join(root, 'fixtures/portal-root-readiness-status/negative-cases.json'), 'utf8'));

test('6 root artifact readinessを一つのread-only観測へ結ぶ', async () => {
  const result = await evaluatePortalRootReadinessStatus(root);
  assert.equal(result.ok, true, result.errors.join(', '));
  const report = result.report;
  assert.equal(report.status, 'blocked');
  assert.deepEqual(report.root, { definitiveStatus: 'root-definitive-incomplete', requiredArtifacts: 6, missingArtifacts: 5, presentArtifacts: 1, distributionStatus: 'not-established' });
  assert.deepEqual(report.artifacts.map((item) => [item.artifactPath, item.prerequisites, item.satisfied, item.blocked, item.observedStatus, item.completionEffect]), [
    ['definitive.yaml', 9, 1, 8, 'missing', 'none'],
    ['surface.inventory.yaml', 8, 2, 6, 'missing', 'none'],
    ['verification.matrix.yaml', 8, 3, 5, 'present', 'none'],
    ['depth.parity.yaml', 6, 1, 5, 'missing', 'none'],
    ['migrations/definitive-v2.yaml', 9, 2, 7, 'missing', 'none'],
    ['evidence/definitive-certificate.json', 10, 1, 9, 'missing', 'none'],
  ]);
  assert.equal(report.boundary.portalIsSubject, false);
  assert.equal(report.boundary.completionEffect, 'none');
});

test('root readinessの分母縮小・artifact present偽装・自動生成/昇格・完成昇格を拒否する', async () => {
  const result = await evaluatePortalRootReadinessStatus(root);
  assert.equal(negative.cases.length, 8);
  for (const item of negative.cases) {
    const checked = validatePortalRootReadinessStatus(applyPortalRootReadinessStatusNegative(result.report, item), result.schema, result.report);
    assert.equal(checked.ok, false, item.caseId);
    assert.ok(checked.errors.includes(item.expectedDiagnostic), `${item.caseId}: ${checked.errors.join(', ')}`);
  }
});

test('browser guardはexact artifact orderとread-only境界が崩れた応答を拒否する', async () => {
  const result = await evaluatePortalRootReadinessStatus(root);
  assert.equal(isPortalRootReadinessStatusSnapshot(result.report), true);
  assert.equal(assertPortalRootReadinessStatusSnapshot(result.report), result.report);
  for (const item of negative.cases) assert.equal(isPortalRootReadinessStatusSnapshot(applyPortalRootReadinessStatusNegative(result.report, item)), false, item.caseId);
  assert.throws(() => assertPortalRootReadinessStatusSnapshot({ status: 'ready' }), /invalid/);
});

test('CLIはroot readiness statusを表示して正本を変更しない', async () => {
  const protectedPaths = [
    'evidence/portal-root-artifact-gap-index.json',
    'evidence/portal-root-depth-parity-readiness.json',
    'evidence/portal-root-migration-readiness.json',
    'evidence/portal-root-definitive-certificate-readiness.json',
    'evidence/portal-root-definitive-declaration-readiness.json',
    'evidence/portal-root-surface-inventory-readiness.json',
    'evidence/portal-root-verification-matrix-readiness.json',
  ];
  const before = Object.fromEntries(await Promise.all(protectedPaths.map(async (relative) => [relative, (await stat(path.join(root, relative))).mtimeMs])));
  const output = spawnSync(process.execPath, ['scripts/atlas-portal.mjs', 'root-readiness-status'], { cwd: root, encoding: 'utf8' });
  assert.equal(output.status, 0, output.stderr);
  const report = JSON.parse(output.stdout);
  assert.equal(report.ok, true);
  assert.equal(report.root.missingArtifacts, 5);
  assert.equal(report.artifacts[0].artifactPath, 'definitive.yaml');
  assert.equal(report.artifacts[5].artifactPath, 'evidence/definitive-certificate.json');
  assert.equal(report.artifacts[2].observedStatus, 'present');
  assert.equal(report.boundary.completionEffect, 'none');
  const unknown = spawnSync(process.execPath, ['scripts/atlas-portal.mjs', 'root-readiness-status', '--promote'], { cwd: root, encoding: 'utf8' });
  assert.equal(unknown.status, 2);
  const after = Object.fromEntries(await Promise.all(protectedPaths.map(async (relative) => [relative, (await stat(path.join(root, relative))).mtimeMs])));
  assert.deepEqual(after, before);
});
