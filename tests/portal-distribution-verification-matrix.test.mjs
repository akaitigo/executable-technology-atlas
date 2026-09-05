import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { applyPortalDistributionVerificationNegative, validatePortalDistributionVerificationMatrix } from '../scripts/lib/portal-distribution-verification-matrix.mjs';
import { DISTRIBUTION_VERIFICATION_CLASSES } from '../scripts/lib/portal-distribution-verification.mjs';

const root=process.cwd();const document=JSON.parse(await readFile(path.join(root,'evidence/portal-distribution-verification-matrix.json'),'utf8'));const schema=JSON.parse(await readFile(path.join(root,'contracts/schemas/portal-distribution-verification-matrix.schema.json'),'utf8'));const fixture=JSON.parse(await readFile(path.join(root,'fixtures/portal-distribution-verification-matrix/negative-cases.json'),'utf8'));

test('Importerの97 Subject×10 classをruntime代替なしで保持する',async()=>{const result=await validatePortalDistributionVerificationMatrix(root,document,schema);assert.equal(result.ok,true,result.errors.join(', '));assert.deepEqual(document.rows.map((row)=>row.classId),DISTRIBUTION_VERIFICATION_CLASSES);assert.deepEqual(result.summary,{subjects:97,classes:10,cells:970,verified:201,gap:478,notEvaluated:291,completionEffect:'none'});assert.equal(document.boundary.coreSubjectArtifact.status,'present');assert.equal(document.boundary.distributionStatus,'not-established');assert.equal(document.boundary.runtimeSubstitution,false);});

test('class/Subject削除・状態格上げ・Gap隠蔽・Runtime代替・Core artifact偽装を拒否する',async()=>{assert.equal(fixture.cases.length,6);for(const item of fixture.cases){const result=await validatePortalDistributionVerificationMatrix(root,applyPortalDistributionVerificationNegative(document,item),schema);assert.equal(result.ok,false,item.caseId);assert.ok(result.errors.includes(item.expectedDiagnostic),`${item.caseId}: ${result.errors.join(', ')}`);}});
