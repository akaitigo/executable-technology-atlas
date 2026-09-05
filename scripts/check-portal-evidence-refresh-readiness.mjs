#!/usr/bin/env node
import { evaluatePortalEvidenceRefreshReadiness, loadPortalEvidenceRefreshPolicy } from './lib/portal-evidence-refresh-readiness.mjs';

const root=process.cwd();
const {policy,schema}=await loadPortalEvidenceRefreshPolicy(root);
const result=await evaluatePortalEvidenceRefreshReadiness(root,policy,schema);
if(!result.ok)throw new Error(`Portal Evidence refresh policy不一致: ${result.errors.join(', ')}`);
const summary=result.report.summary;
console.log(`Portal Evidence refresh readiness: PASS / status=${result.report.status} / stale wrappers=${summary.staleWrappers}/${summary.wrappers} / changed inputs=${summary.inputsChangedSinceRun}/${summary.inputs} / missing outputs=${summary.missingDiscoveredOutputs} / completion_effect=none`);
