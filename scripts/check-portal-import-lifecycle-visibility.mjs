#!/usr/bin/env node
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { buildPortalImportLifecycleVisibility, loadPortalImportLifecycleInputs, validatePortalImportLifecycleVisibility } from './lib/portal-import-lifecycle-visibility.mjs';

const root=process.cwd();const mode=process.argv[2]??'--check';const output=path.join(root,'evidence/portal-import-lifecycle-visibility.json');
if(!['--check','--record'].includes(mode))throw new Error('使い方: node scripts/check-portal-import-lifecycle-visibility.mjs --check|--record');
const inputs=await loadPortalImportLifecycleInputs(root);if(mode==='--record')await writeFile(output,`${JSON.stringify(buildPortalImportLifecycleVisibility(inputs),null,2)}\n`);
const document=JSON.parse(await readFile(output,'utf8'));const result=await validatePortalImportLifecycleVisibility(root,document,inputs.schema);if(!result.ok)throw new Error(`Portal Import Lifecycle Visibility不一致: ${result.errors.join(', ')}`);
console.log(`Portal Import Lifecycle Visibility: PASS / verified=${result.summary.verified} / quarantined=${result.summary.quarantined} / absent=${result.summary.absent} / incomplete=${result.summary.incompleteCurrentReleases} / expired=${result.summary.expiredHistoricalReleases} / fixture=${result.summary.fixtureCoverage.failureScenarios}`);
