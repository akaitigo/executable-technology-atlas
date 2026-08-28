#!/usr/bin/env node
import { mkdir, rename, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { evaluateNonRegression } from './lib/non-regression.mjs';

const root = process.cwd();
const output = path.resolve(process.argv[2] ?? path.join(root, 'evidence', 'non-regression-report.json'));
const report = await evaluateNonRegression(root);
await mkdir(path.dirname(output), { recursive: true });
const temporary = `${output}.tmp`;
await writeFile(temporary, `${JSON.stringify(report, null, 2)}\n`);
await rename(temporary, output);
console.log(`Non-regression: ${report.verdict} / ${report.summary.baselineSubjects} subjects / ${report.summary.baselineTargets} targets / ${report.summary.baselineEvidence} evidence / violations=${report.summary.violations}`);
if (report.verdict !== 'pass') process.exitCode = 1;
