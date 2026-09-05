import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { applyPortalDistributionBindingNegative, validatePortalDistributionInputBindings } from '../scripts/lib/portal-distribution-input-bindings.mjs';

const root=process.cwd();
const document=JSON.parse(await readFile(path.join(root,'evidence/portal-distribution-input-bindings.json'),'utf8'));
const schema=JSON.parse(await readFile(path.join(root,'contracts/schemas/portal-distribution-input-bindings.schema.json'),'utf8'));
const fixture=JSON.parse(await readFile(path.join(root,'fixtures/portal-distribution-input-bindings/negative-cases.json'),'utf8'));

test('97 Subjectの固定Release/clean commit入力を実artifactへ結び、欠落を維持する',async()=>{
  const result=await validatePortalDistributionInputBindings(root,document,schema);assert.equal(result.ok,true,result.errors.join(', '));assert.deepEqual(result.summary,{subjects:97,releaseBindings:7,fixedCommitAuditBindings:7,definitiveV2Bindings:0,publicTrustedReleaseBindings:0,unboundReleaseSubjects:90,unboundDefinitiveSubjects:97});assert.equal(document.status,'incomplete');assert.deepEqual(document.boundary,{readOnly:true,autoPromotion:false,defaultBranchDependency:false,activeSubjectTreeDependency:false,distributionGapEffect:'none',completionEffect:'none'});
});

test('分母縮小、identity/tree改変、branch依存、Definitive捏造、Gap削除、完成格上げを拒否する',async()=>{
  assert.equal(fixture.cases.length,7);for(const item of fixture.cases){const result=await validatePortalDistributionInputBindings(root,applyPortalDistributionBindingNegative(document,item),schema);assert.equal(result.ok,false,item.caseId);assert.ok(result.errors.includes(item.expectedDiagnostic),`${item.caseId}: ${result.errors.join(', ')}`);}
});
