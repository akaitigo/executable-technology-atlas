import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { assertPortalImportLifecycleSnapshot, isPortalImportLifecycleSnapshot } from '../app/lib/portal-import-lifecycle-visibility.mjs';
import { applyPortalImportLifecycleNegative, evaluatePortalImportLifecycleVisibility, validatePortalImportLifecycleVisibility } from '../scripts/lib/portal-import-lifecycle-visibility.mjs';

const root=process.cwd();
const schema=JSON.parse(await readFile(path.join(root,'contracts/schemas/portal-import-lifecycle-visibility.schema.json'),'utf8'));
const document=JSON.parse(await readFile(path.join(root,'evidence/portal-import-lifecycle-visibility.json'),'utf8'));
const negative=JSON.parse(await readFile(path.join(root,'fixtures/portal-import-lifecycle-visibility/negative-cases.json'),'utf8'));

test('97 Subjectの実Import lifecycleとfixture検証を混同せず固定する',async()=>{
  const result=await validatePortalImportLifecycleVisibility(root,document,schema);assert.equal(result.ok,true,result.errors.join(', '));
  assert.deepEqual(document.actual,{subjects:97,verified:7,quarantined:0,absent:90,incompleteCurrentReleases:7,publicTrustedCurrentReleases:0,expiredHistoricalReleases:0,supersededHistoricalReleases:0,archivedHistoricalReleases:0,staleHumanReviewHolds:3,definitiveV2Imports:0});
  assert.equal(document.subjects.length,97);assert.equal(document.fixtureCoverage.fixtureOnly,true);assert.equal(document.fixtureCoverage.failureScenarios,11);assert.equal(document.fixtureCoverage.registryNegativeCases,14);
  assert.deepEqual(document.boundary,{readOnly:true,fixtureIsActual:false,negativeCoverageIsProgress:false,staleLockAccepted:false,revokedLockAccepted:false,hideIncomplete:false,hideExpired:false,autoPromotion:false,distributionStatus:'not-established',completionEffect:'none'});
});

test('fixture実状態化・未収集/未完成隠蔽・stale/revoked許容・自動昇格を拒否する',async()=>{
  assert.equal(negative.cases.length,7);
  for(const item of negative.cases){const result=await validatePortalImportLifecycleVisibility(root,applyPortalImportLifecycleNegative(document,item),schema);assert.equal(result.ok,false,item.caseId);assert.ok(result.errors.includes(item.expectedDiagnostic),`${item.caseId}: ${result.errors.join(', ')}`);}
});

test('browser guardは実Import countsとstale/revoked拒否境界が崩れた応答を拒否する',async()=>{
  const result=await evaluatePortalImportLifecycleVisibility(root);
  assert.equal(result.ok,true,result.errors.join(', '));
  assert.equal(isPortalImportLifecycleSnapshot(result.report),true);
  assert.equal(assertPortalImportLifecycleSnapshot(result.report),result.report);
  for(const item of negative.cases)assert.equal(isPortalImportLifecycleSnapshot(applyPortalImportLifecycleNegative(result.report,item)),false,item.caseId);
  assert.throws(()=>assertPortalImportLifecycleSnapshot({status:'complete'}),/invalid/);
});

test('CLIはImport lifecycleを表示して正本を変更しない',async()=>{
  const protectedPaths=['evidence/import-report.json','evidence/portal-import-lifecycle-visibility.json','app/data/index.generated.json','app/data/index-bootstrap.generated.json'];
  const before=Object.fromEntries(await Promise.all(protectedPaths.map(async(relative)=>[relative,(await stat(path.join(root,relative))).mtimeMs])));
  const output=spawnSync(process.execPath,['scripts/atlas-portal.mjs','import-lifecycle'],{cwd:root,encoding:'utf8'});
  assert.equal(output.status,0,output.stderr);
  const report=JSON.parse(output.stdout);
  assert.equal(report.ok,true);
  assert.equal(report.status,'incomplete');
  assert.equal(report.actual.subjects,97);
  assert.equal(report.actual.verified,7);
  assert.equal(report.fixtureCoverage.registryNegativeCases,14);
  assert.equal(report.boundary.completionEffect,'none');
  const unknown=spawnSync(process.execPath,['scripts/atlas-portal.mjs','import-lifecycle','--promote'],{cwd:root,encoding:'utf8'});
  assert.equal(unknown.status,2);
  const after=Object.fromEntries(await Promise.all(protectedPaths.map(async(relative)=>[relative,(await stat(path.join(root,relative))).mtimeMs])));
  assert.deepEqual(after,before);
});
