#!/usr/bin/env node
import { evaluatePortalRootReadinessStatus } from './lib/portal-root-readiness-status.mjs';

const result = await evaluatePortalRootReadinessStatus(process.cwd());
const report = result.report;
console.log(`Portal root readiness status: ${result.ok ? 'PASS' : 'FAIL'} / root missing=${report.root.missingArtifacts}/${report.root.requiredArtifacts} / declaration=${report.artifacts[0].blocked} blocked / surface=${report.artifacts[1].blocked} blocked / matrix=${report.artifacts[2].blocked} blocked / completion_effect=${report.boundary.completionEffect}`);
if (!result.ok) {
  for (const error of result.errors) console.error(error);
  process.exitCode = 1;
}
