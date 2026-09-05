import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { applyPortalDistributionNegative, validatePortalDistributionReadiness } from '../scripts/lib/portal-distribution-readiness.mjs';

const root=process.cwd();
const schema=JSON.parse(await readFile(path.join(root,'contracts/schemas/portal-distribution-readiness.schema.json'),'utf8'));
const document=JSON.parse(await readFile(path.join(root,'evidence/portal-distribution-readiness.json'),'utf8'));
const negative=JSON.parse(await readFile(path.join(root,'fixtures/portal-distribution-readiness/negative-cases.json'),'utf8'));

test('97 Subjectの配布状態を実Indexから個別にfail-closed投影する',async()=>{
  const result=await validatePortalDistributionReadiness(root,document,schema);assert.equal(result.ok,true,result.errors.join(', '));
  assert.deepEqual(result.summary,{subjects:97,distributionReady:0,releasePresent:7,publicTrustedRelease:0,definitiveV2InputAvailable:0,definitiveCoreGatePassed:0,definitiveCertificatePresent:0,fixedCommitAuditAvailable:7,blockerInstances:589});
  assert.equal(document.status,'not-established');assert.equal(document.subjects.length,97);assert.equal(document.subjects.every((item)=>item.distribution.status==='blocked'&&!item.distribution.eligible&&item.distribution.blockerIds.length>0),true);
  assert.deepEqual(document.boundary,{readOnly:true,autoPromotion:false,rawCountsAreCompletion:false,portalBoundedCertificateEffect:'none',subjectDefinitiveEffect:'none',distributionGapEffect:'none',completionEffect:'none'});
});

test('Subject削除・Gap集約・fixture Release昇格・raw件数完成を拒否する',async()=>{
  assert.equal(negative.cases.length,5);
  for(const item of negative.cases){const result=await validatePortalDistributionReadiness(root,applyPortalDistributionNegative(document,item),schema);const expected=item.expectedDiagnostic??item.expectedDiagnosticPrefix;assert.equal(result.ok,false,item.caseId);assert.ok(result.errors.includes(expected),`${item.caseId}: ${result.errors.join(', ')}`);}
});
