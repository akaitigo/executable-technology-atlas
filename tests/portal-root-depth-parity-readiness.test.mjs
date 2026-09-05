import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { applyPortalRootDepthParityNegative, validatePortalRootDepthParityReadiness } from '../scripts/lib/portal-root-depth-parity-readiness.mjs';

const root=process.cwd();const schema=JSON.parse(await readFile(path.join(root,'contracts/schemas/portal-root-depth-parity-readiness.schema.json'),'utf8'));const document=JSON.parse(await readFile(path.join(root,'evidence/portal-root-depth-parity-readiness.json'),'utf8'));const negative=JSON.parse(await readFile(path.join(root,'fixtures/portal-root-depth-parity-readiness/negative-cases.json'),'utf8'));

test('Portal depth parity readinessはCore Subject artifact欠落と6 prerequisiteを保持する',async()=>{const result=await validatePortalRootDepthParityReadiness(root,document,schema);assert.equal(result.ok,true,result.errors.join(', '));assert.deepEqual(result.summary,{prerequisites:6,satisfied:1,blocked:5,coreDepthParityArtifactsPresent:0,completionEffect:'none'});assert.equal(document.coreContract.artifactPath,'depth.parity.yaml');assert.equal(document.coreContract.observedStatus,'missing');assert.equal(document.observed.portalIsSubject,false);assert.equal(document.observed.dependencyGraph.requiredOutputDenominator,6);assert.equal(document.observed.dependencyGraph.boundRequiredOutputs+document.observed.dependencyGraph.missingRequiredOutputs.length,6);assert.equal(document.boundary.recordedGraphStatusIsCurrentProof,false);assert.equal(document.boundary.completionEffect,'none');});

test('分母縮小・Core artifact偽装・Portal adapter代替・Graph格上げ・完成昇格を拒否する',async()=>{assert.equal(negative.cases.length,6);for(const item of negative.cases){const result=await validatePortalRootDepthParityReadiness(root,applyPortalRootDepthParityNegative(document,item),schema);assert.equal(result.ok,false,item.caseId);assert.ok(result.errors.includes(item.expectedDiagnostic),`${item.caseId}: ${result.errors.join(', ')}`);}});
