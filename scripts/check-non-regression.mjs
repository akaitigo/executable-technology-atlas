#!/usr/bin/env node
import { mkdir, readFile, rename, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { evaluateNonRegression } from './lib/non-regression.mjs';
import { sha256 } from './lib/crypto.mjs';

const root = process.cwd();
const output = path.resolve(process.argv[2] ?? path.join(root, 'evidence', 'non-regression-report.json'));
const report = await evaluateNonRegression(root);
const harnessPath = path.join(root, 'evidence', 'non-regression-harness.json');
const componentPaths = ['scripts/check-non-regression.mjs','scripts/lib/non-regression.mjs','scripts/lib/neutral-language.mjs','scripts/lib/depth-reference.mjs','scripts/lib/authority-review.mjs','scripts/lib/evidence-dependency.mjs','scripts/lib/definitive-v2.mjs','scripts/lib/fixed-commit-audit.mjs','tests/importer.test.mjs','tests/definitive-v2.test.mjs','tests/fixed-commit-audit.test.mjs','tests/non-regression.test.mjs','contracts/non-regression-baseline.json','contracts/non-regression-mappings.json','contracts/depth-reference-lock.json','contracts/authority-review-lock.json','contracts/evidence-dependency-lock.json','contracts/definitive-v2-lock.json','contracts/fixed-commit-audit-lock.json','contracts/fixed-commit-audit-postgresql-lock.json','contracts/fixed-commit-audit-flutter-lock.json','contracts/fixed-commit-audit-rabbitmq-lock.json','contracts/fixed-commit-audit-kotlin-lock.json','contracts/fixed-commit-audit-zero-trust-lock.json','contracts/fixed-commit-audit-frontend-behavior-lock.json','contracts/schemas/evidence-dependency-graph.schema.json','contracts/schemas/definitive.schema.json','contracts/schemas/definitive-migration.schema.json','contracts/schemas/definitive-certificate.schema.json','contracts/schemas/fixed-commit-audit.schema.json','contracts/reference/EVIDENCE_DEPENDENCY_GRAPH.md','contracts/reference/MIGRATION_DEFINITIVE_V2.md'];
const harness = { schemaVersion: 1, generatedAt: report.generatedAt, components: await Promise.all(componentPaths.map(async (file) => ({ path:file, digest:sha256(await readFile(path.join(root,file))) }))) };
await mkdir(path.dirname(output), { recursive: true });
const harnessTemporary = `${harnessPath}.tmp`;
await writeFile(harnessTemporary, `${JSON.stringify(harness, null, 2)}\n`);
await rename(harnessTemporary, harnessPath);
const temporary = `${output}.tmp`;
await writeFile(temporary, `${JSON.stringify(report, null, 2)}\n`);
await rename(temporary, output);
console.log(`Non-regression: ${report.verdict} / ${report.summary.baselineSubjects} subjects / ${report.summary.baselineTargets} targets / ${report.summary.baselineEvidence} evidence / violations=${report.summary.violations}`);
if (report.verdict !== 'pass') process.exitCode = 1;
