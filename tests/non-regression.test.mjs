import assert from 'node:assert/strict';
import { cp, mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { evaluateNonRegression } from '../scripts/lib/non-regression.mjs';

const root = process.cwd();
const readJson = async (file) => JSON.parse(await readFile(file, 'utf8'));
const writeJson = async (file, value) => writeFile(file, `${JSON.stringify(value, null, 2)}\n`);

test('凍結Baselineは97 Subject・246 Target・45 Evidenceを個別に保護する', async () => {
  const result = await evaluateNonRegression(root);
  assert.equal(result.verdict, 'pass');
  assert.deepEqual({ subjects:result.summary.baselineSubjects, targets:result.summary.baselineTargets, evidence:result.summary.baselineEvidence, failures:result.summary.failureScenarios }, { subjects:97, targets:246, evidence:45, failures:11 });
});

test('削除・格上げ・不可視化・粒度低下を拒否する', async () => {
  const temporary = await mkdtemp(path.join(os.tmpdir(), 'atlas-non-regression-'));
  try {
    for (const directory of ['contracts','contracts/reference','app/data','fixtures/depth-references','fixtures/fixed-commit-audits','public/data/releases','public/data/authority-reviews','public/data/fixed-commit-audits','public/data/index']) await mkdir(path.join(temporary,directory), { recursive:true });
    for (const file of ['contracts/non-regression-baseline.json','contracts/non-regression-mappings.json','contracts/depth-reference-lock.json','contracts/authority-review-lock.json','contracts/evidence-dependency-lock.json','contracts/definitive-v2-lock.json','contracts/fixed-commit-audit-lock.json','contracts/fixed-commit-audit-postgresql-lock.json','contracts/fixed-commit-audit-flutter-lock.json','contracts/fixed-commit-audit-rabbitmq-lock.json','contracts/fixed-commit-audit-kotlin-lock.json','contracts/reference/MIGRATION_DEFINITIVE_V2.md','app/data/index.generated.json','app/data/index-bootstrap.generated.json','fixtures/failure-scenarios.json','fixtures/registry.json','app/page.tsx']) {
      await mkdir(path.dirname(path.join(temporary,file)), { recursive:true });
      await cp(path.join(root,file), path.join(temporary,file));
    }
    await cp(path.join(root,'public/data/releases'), path.join(temporary,'public/data/releases'), { recursive:true });
    await cp(path.join(root,'public/data/authority-reviews'), path.join(temporary,'public/data/authority-reviews'), { recursive:true });
    await cp(path.join(root,'public/data/fixed-commit-audits'), path.join(temporary,'public/data/fixed-commit-audits'), { recursive:true });
    await cp(path.join(root,'public/data/index'), path.join(temporary,'public/data/index'), { recursive:true });
    await cp(path.join(root,'fixtures/depth-references'), path.join(temporary,'fixtures/depth-references'), { recursive:true });
    await cp(path.join(root,'fixtures/fixed-commit-audits'), path.join(temporary,'fixtures/fixed-commit-audits'), { recursive:true });
    const indexPath = path.join(temporary,'app/data/index.generated.json');
    const failuresPath = path.join(temporary,'fixtures/failure-scenarios.json');
    const mappingsPath = path.join(temporary,'contracts/non-regression-mappings.json');
    const pagePath = path.join(temporary,'app/page.tsx');
    const bootstrapPath=path.join(temporary,'app/data/index-bootstrap.generated.json');
    const originalIndex = await readJson(indexPath);
    const originalBootstrap=await readJson(bootstrapPath);
    const publicIndexPath=path.join(temporary,`public${originalBootstrap.publicUrl}`);
    const originalPublicIndex=await readFile(publicIndexPath);
    const originalFailures = await readJson(failuresPath);
    const originalMappings = await readJson(mappingsPath);
    const originalPage = await readFile(pagePath,'utf8');
    const expectViolation = async (code) => { const result=await evaluateNonRegression(temporary,{scanLanguage:false});assert.equal(result.verdict,'fail');assert.ok(result.violations.some((item)=>item.code===code),`${code}: ${JSON.stringify(result.violations)}`); };

    const withoutSubject=structuredClone(originalIndex);withoutSubject.subjects.shift();await writeJson(indexPath,withoutSubject);await expectViolation('subject-deleted');await writeJson(indexPath,originalIndex);
    const replacedSubject=structuredClone(originalIndex);replacedSubject.subjects[0].repository='replacement-without-old-id-mapping';await writeJson(indexPath,replacedSubject);await expectViolation('subject-identity-replaced-without-mapping');await writeJson(indexPath,originalIndex);
    const promoted=structuredClone(originalIndex);const planned=promoted.subjects.find((subject)=>subject.status==='planned');planned.status='complete';await writeJson(indexPath,promoted);await expectViolation('catalog-status-promoted');await writeJson(indexPath,originalIndex);
    const bounded=structuredClone(originalIndex);bounded.subjects.find((subject)=>subject.release).releaseHistory[0].completion={classification:'bounded-historical',definitive:true,certificateSchemaVersion:1};await writeJson(indexPath,bounded);await expectViolation('bounded-promoted-to-definitive');await writeJson(indexPath,originalIndex);
    const releasePromoted=structuredClone(originalIndex);releasePromoted.subjects.find((subject)=>subject.release).releaseHistory[0].status='complete';await writeJson(indexPath,releasePromoted);await expectViolation('release-history-status-rewritten');await writeJson(indexPath,originalIndex);

    const targetSubject=originalIndex.subjects.find((subject)=>subject.release?.coverage.required>0);const targetDetailPath=path.join(temporary,'public',targetSubject.release.detailUrl);const targetDetail=await readJson(targetDetailPath);const originalTargetDetail=structuredClone(targetDetail);targetDetail.targets.shift();await writeJson(targetDetailPath,targetDetail);await expectViolation('target-history-deleted');await writeJson(targetDetailPath,originalTargetDetail);
    const targetRewritten=structuredClone(originalTargetDetail);targetRewritten.targets[0].state=targetRewritten.targets[0].state==='covered'?'planned':'covered';await writeJson(targetDetailPath,targetRewritten);await expectViolation('target-history-status-rewritten');await writeJson(targetDetailPath,originalTargetDetail);
    const evidenceSubject=originalIndex.subjects.find((subject)=>subject.release?.evidenceCount>0);const evidenceDetailPath=path.join(temporary,'public',evidenceSubject.release.detailUrl);const evidenceDetail=await readJson(evidenceDetailPath);const originalEvidenceDetail=structuredClone(evidenceDetail);evidenceDetail.evidence.shift();await writeJson(evidenceDetailPath,evidenceDetail);await expectViolation('evidence-history-deleted');await writeJson(evidenceDetailPath,originalEvidenceDetail);
    const evidenceRewritten=structuredClone(originalEvidenceDetail);evidenceRewritten.evidence[0].verdict=evidenceRewritten.evidence[0].verdict==='pass'?'fail':'pass';await writeJson(evidenceDetailPath,evidenceRewritten);await expectViolation('evidence-history-rewritten');await writeJson(evidenceDetailPath,originalEvidenceDetail);

    const failures=structuredClone(originalFailures);failures.scenarios=failures.scenarios.filter((scenario)=>scenario.id!=='coverage-infeasible');await writeJson(failuresPath,failures);await expectViolation('failure-scenario-deleted');await writeJson(failuresPath,originalFailures);
    await writeFile(pagePath,originalPage.replace("const [status, setStatus] = useState('')","const [status, setStatus] = useState('release:complete')"));await expectViolation('filter-default-excludes');await writeFile(pagePath,originalPage);
    const mappings=structuredClone(originalMappings);mappings.subjectMappings.push({from:originalIndex.subjects[0].id,to:originalIndex.subjects[0].id});await writeJson(mappingsPath,mappings);await expectViolation('invalid-subject-mapping');await writeJson(mappingsPath,originalMappings);
    const depthSubject=originalIndex.subjects.find((subject)=>subject.id==='frontend-behavior');const depthDetailPath=path.join(temporary,'public',depthSubject.release.detailUrl);const depthDetail=await readJson(depthDetailPath);const originalDepthDetail=structuredClone(depthDetail);depthDetail.depthReference.axes.shift();await writeJson(depthDetailPath,depthDetail);await expectViolation('depth-reference-axis-information-reduced');await writeJson(depthDetailPath,originalDepthDetail);
    const depthPromoted=structuredClone(originalIndex);depthPromoted.subjects.find((subject)=>subject.id==='frontend-behavior').depthReference.completion.definitive=true;await writeJson(indexPath,depthPromoted);await expectViolation('depth-reference-status-promoted');await writeJson(indexPath,originalIndex);
    const reviewProgress=structuredClone(originalIndex);const reviewSubject=reviewProgress.subjects.find((subject)=>subject.id==='frontend-behavior');reviewSubject.authorityReview.summary.human_reviewed=1;reviewSubject.authorityReview.summary.has_human_progress=true;await writeJson(indexPath,reviewProgress);await expectViolation('authority-review-summary-rewritten');await writeJson(indexPath,originalIndex);
    const dependencyPromoted=structuredClone(originalIndex);dependencyPromoted.subjects[0].evidenceDependency={...dependencyPromoted.subjects[0].evidenceDependency,availability:'missing',status:'current',autoPromotion:true,coreGate:{...dependencyPromoted.subjects[0].evidenceDependency.coreGate,result:'pass'}};await writeJson(indexPath,dependencyPromoted);await expectViolation('evidence-dependency-write-boundary-weakened');await writeJson(indexPath,originalIndex);
    const definitivePromoted=structuredClone(originalIndex);definitivePromoted.subjects[0].definitiveV2={...definitivePromoted.subjects[0].definitiveV2,availability:'missing',status:'subject-definitive',autoPromotion:true,coreGate:{...definitivePromoted.subjects[0].definitiveV2.coreGate,result:'pass'}};await writeJson(indexPath,definitivePromoted);await expectViolation('definitive-v2-write-boundary-weakened');await writeJson(indexPath,originalIndex);
    const definitiveAggregated=structuredClone(originalIndex);definitiveAggregated.definitiveV2Summary.gapCounts=[];definitiveAggregated.definitiveV2Summary.gapInstances=0;await writeJson(indexPath,definitiveAggregated);await expectViolation('definitive-v2-summary-information-reduced');await writeJson(indexPath,originalIndex);
    const definitiveGapHidden=structuredClone(originalIndex);definitiveGapHidden.subjects[0].definitiveV2.gapIds.pop();await writeJson(indexPath,definitiveGapHidden);await expectViolation('definitive-v2-gap-information-reduced');await writeJson(indexPath,originalIndex);
    const fixedAuditPromoted=structuredClone(originalIndex);const audited=fixedAuditPromoted.subjects.find((subject)=>subject.fixedCommitAudit);audited.fixedCommitAudit.autoPromotion=true;await writeJson(indexPath,fixedAuditPromoted);await expectViolation('fixed-commit-audit-promoted');await writeJson(indexPath,originalIndex);
    const fixedAuditGapHidden=structuredClone(originalIndex);fixedAuditGapHidden.subjects.find((subject)=>subject.fixedCommitAudit).fixedCommitAudit.gapCount-=1;await writeJson(indexPath,fixedAuditGapHidden);await expectViolation('fixed-commit-audit-gaps-reduced');await writeJson(indexPath,originalIndex);
    const bootstrapPromoted=structuredClone(originalBootstrap);bootstrapPromoted.completionSummary.subjectDefinitive=97;await writeJson(bootstrapPath,bootstrapPromoted);await expectViolation('index-bootstrap-fail-closed');await writeJson(bootstrapPath,originalBootstrap);
    await writeFile(publicIndexPath,Buffer.concat([originalPublicIndex,Buffer.from(' ')]));await expectViolation('content-addressed-index-bytes');await writeFile(publicIndexPath,originalPublicIndex);
    assert.equal((await evaluateNonRegression(temporary,{scanLanguage:false})).verdict,'pass');
  } finally {
    await rm(temporary,{recursive:true,force:true});
  }
});
