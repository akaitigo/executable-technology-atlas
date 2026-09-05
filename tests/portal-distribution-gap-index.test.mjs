import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { applyPortalDistributionGapNegative, validatePortalDistributionGapIndex } from '../scripts/lib/portal-distribution-gap-index.mjs';

const root=process.cwd();const document=JSON.parse(await readFile(path.join(root,'evidence/portal-distribution-gap-index.json'),'utf8'));const schema=JSON.parse(await readFile(path.join(root,'contracts/schemas/portal-distribution-gap-index.schema.json'),'utf8'));const fixture=JSON.parse(await readFile(path.join(root,'fixtures/portal-distribution-gap-index/negative-cases.json'),'utf8'));

test('97 Subjectの589 Distribution Gapを一件ずつopenで保持する',async()=>{const result=await validatePortalDistributionGapIndex(root,document,schema);assert.equal(result.ok,true,result.errors.join(', '));assert.deepEqual(result.summary.gapCounts,[{blockerId:'authority-inventory-closure-not-established',openInstances:97},{blockerId:'definitive-certificate-missing',openInstances:97},{blockerId:'definitive-core-gate-not-passed',openInstances:97},{blockerId:'definitive-v2-input-missing',openInstances:97},{blockerId:'evidence-dependency-not-current',openInstances:97},{blockerId:'public-trust-missing',openInstances:7},{blockerId:'release-manifest-incomplete',openInstances:7},{blockerId:'signed-fixed-release-missing',openInstances:90}]);assert.equal(result.summary.openInstances,589);assert.equal(result.summary.closedInstances,0);assert.equal(document.boundary.distributionStatus,'not-established');assert.equal(document.boundary.completionEffect,'none');});

test('Gap削除・集約・付替え・source移動・根拠なしclose・件数完成を拒否する',async()=>{assert.equal(fixture.cases.length,6);for(const item of fixture.cases){const result=await validatePortalDistributionGapIndex(root,applyPortalDistributionGapNegative(document,item),schema);assert.equal(result.ok,false,item.caseId);assert.ok(result.errors.includes(item.expectedDiagnostic),`${item.caseId}: ${result.errors.join(', ')}`);}});
