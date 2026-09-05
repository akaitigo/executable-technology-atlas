#!/usr/bin/env node
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { buildPortalDistributionReadiness, loadPortalDistributionInputs, validatePortalDistributionReadiness } from './lib/portal-distribution-readiness.mjs';

const root=process.cwd();const mode=process.argv[2]??'--check';const output=path.join(root,'evidence/portal-distribution-readiness.json');
if(!['--check','--record'].includes(mode))throw new Error('使い方: node scripts/check-portal-distribution-readiness.mjs --check|--record');
const inputs=await loadPortalDistributionInputs(root);if(mode==='--record')await writeFile(output,`${JSON.stringify(buildPortalDistributionReadiness(inputs.index,inputs.indexBytes),null,2)}\n`);
const document=JSON.parse(await readFile(output,'utf8'));const result=await validatePortalDistributionReadiness(root,document,inputs.schema);if(!result.ok)throw new Error(`Portal Distribution Readiness不一致: ${result.errors.join(', ')}`);
console.log(`Portal Distribution Readiness: PASS / ready=${result.summary.distributionReady}/${result.summary.subjects} / release=${result.summary.releasePresent} / public-trust=${result.summary.publicTrustedRelease} / definitive-input=${result.summary.definitiveV2InputAvailable} / certificate=${result.summary.definitiveCertificatePresent} / blockers=${result.summary.blockerInstances}`);
