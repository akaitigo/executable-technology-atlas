#!/usr/bin/env node
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { buildPortalRootDepthParityReadiness, loadPortalRootDepthParityInputs, validatePortalRootDepthParityReadiness } from './lib/portal-root-depth-parity-readiness.mjs';
import { preserveRecordedGraphSnapshot } from './lib/recorded-graph-snapshot.mjs';

const root=process.cwd();const mode=process.argv[2]??'--check';const output=path.join(root,'evidence/portal-root-depth-parity-readiness.json');
if(!['--check','--record'].includes(mode))throw new Error('使い方: node scripts/check-portal-root-depth-parity-readiness.mjs --check|--record');
const inputs=await loadPortalRootDepthParityInputs(root);if(mode==='--record'){const next=await preserveRecordedGraphSnapshot(output,buildPortalRootDepthParityReadiness(inputs));await writeFile(output,`${JSON.stringify(next,null,2)}\n`);}
const document=JSON.parse(await readFile(output,'utf8'));const result=await validatePortalRootDepthParityReadiness(root,document,inputs.schema);if(!result.ok)throw new Error(`Portal root Depth parity readiness不一致: ${result.errors.join(', ')}`);
console.log(`Portal root Depth parity readiness: PASS / blocked=${result.summary.blocked}/${result.summary.prerequisites} / Core artifact present=${result.summary.coreDepthParityArtifactsPresent} / completion_effect=${result.summary.completionEffect}`);
