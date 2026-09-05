import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { loadTrust } from '../scripts/lib/validate.mjs';
import { projectFixedCommitAudit, validateFixedCommitAudit } from '../scripts/lib/fixed-commit-audit.mjs';

const root=process.cwd();
const lock=JSON.parse(await readFile(path.join(root,'contracts/fixed-commit-audit-lock.json'),'utf8'));
const schema=JSON.parse(await readFile(path.join(root,lock.schemaPath),'utf8'));
const envelope=JSON.parse(await readFile(path.join(root,lock.fixturePath),'utf8'));
const trusted=await loadTrust(path.join(root,'fixtures'));
const postgresqlLock=JSON.parse(await readFile(path.join(root,'contracts/fixed-commit-audit-postgresql-lock.json'),'utf8'));
const postgresqlEnvelope=JSON.parse(await readFile(path.join(root,postgresqlLock.fixturePath),'utf8'));
const flutterLock=JSON.parse(await readFile(path.join(root,'contracts/fixed-commit-audit-flutter-lock.json'),'utf8'));
const flutterEnvelope=JSON.parse(await readFile(path.join(root,flutterLock.fixturePath),'utf8'));
const rabbitmqLock=JSON.parse(await readFile(path.join(root,'contracts/fixed-commit-audit-rabbitmq-lock.json'),'utf8'));
const rabbitmqEnvelope=JSON.parse(await readFile(path.join(root,rabbitmqLock.fixturePath),'utf8'));
const kotlinLock=JSON.parse(await readFile(path.join(root,'contracts/fixed-commit-audit-kotlin-lock.json'),'utf8'));
const kotlinEnvelope=JSON.parse(await readFile(path.join(root,kotlinLock.fixturePath),'utf8'));
const zeroTrustLock=JSON.parse(await readFile(path.join(root,'contracts/fixed-commit-audit-zero-trust-lock.json'),'utf8'));
const zeroTrustEnvelope=JSON.parse(await readFile(path.join(root,zeroTrustLock.fixturePath),'utf8'));
const frontendBehaviorLock=JSON.parse(await readFile(path.join(root,'contracts/fixed-commit-audit-frontend-behavior-lock.json'),'utf8'));
const frontendBehaviorEnvelope=JSON.parse(await readFile(path.join(root,frontendBehaviorLock.fixturePath),'utf8'));

test('実Subject固定commit監査EnvelopeをSchema・Digest・署名で受理する',()=>{
  const result=validateFixedCommitAudit(envelope,schema,trusted);
  assert.equal(result.ok,true,result.errors.join('; '));
  assert.equal(result.digest,lock.attestationDigest);
  assert.equal(result.trust.usage,'fixture-only');
});

test('Git objectとRelease未成立境界を固定する',()=>{
  const audit=projectFixedCommitAudit(envelope,validateFixedCommitAudit(envelope,schema,trusted));
  assert.deepEqual({commit:audit.source.commit,tree:audit.source.tree},{commit:lock.sourceCommit,tree:lock.sourceTree});
  assert.deepEqual(audit.releaseBoundary,{status:'unpublished-fixed-commit',tag:null,signedManifest:false,publicTrustKey:false,definitiveCertificate:false});
  assert.deepEqual({status:audit.manifest.status,openRequired:audit.manifest.openRequired},{status:'incomplete',openRequired:22});
  assert.equal(audit.readOnly,true);
  assert.equal(audit.autoPromotion,false);
});

test('Core Gate結果とAuthorityの分母を粒度を落とさず保持する',()=>{
  const audit=projectFixedCommitAudit(envelope,validateFixedCommitAudit(envelope,schema,trusted));
  assert.deepEqual({result:audit.core.evidenceDependency.result,...audit.core.evidenceDependency.summary},{result:'pass',inputs:15,changedInputs:0,outputs:1060,affectedOutputs:0,runs:30});
  assert.equal(audit.core.definitive.result,'fail');
  assert.deepEqual({anchors:audit.core.authorityBody.summary.candidateAnchors,unclassified:audit.core.authorityBody.summary.unclassified,reviewed:audit.core.authorityBody.summary.humanReviewed,decisions:audit.core.authorityReview.summary.decisions},{anchors:63889,unclassified:63889,reviewed:0,decisions:0});
});

test('固定commitの既知Gapを順序付きで保持する',()=>{
  const audit=projectFixedCommitAudit(envelope,validateFixedCommitAudit(envelope,schema,trusted));
  assert.deepEqual(audit.gaps.map((gap)=>gap.id),lock.requiredGapIds);
  assert.equal(audit.gaps.find((gap)=>gap.id==='authority-human-review-open').count,63889);
  assert.equal(audit.gaps.find((gap)=>gap.id==='open-required-targets').count,22);
});

test('PostgreSQL固定commitのTarget・Authority・Scenario Gapを保持する',()=>{
  const validated=validateFixedCommitAudit(postgresqlEnvelope,schema,trusted);
  assert.equal(validated.ok,true,validated.errors.join('; '));
  const audit=projectFixedCommitAudit(postgresqlEnvelope,validated);
  assert.deepEqual({commit:audit.source.commit,tree:audit.source.tree},{commit:postgresqlLock.sourceCommit,tree:postgresqlLock.sourceTree});
  assert.deepEqual({openRequired:audit.manifest.openRequired,unclassified:audit.core.authorityBody.summary.unclassified,pending:audit.core.authorityReview.summary.pendingHuman,decisions:audit.core.authorityReview.summary.decisions},{openRequired:27,unclassified:5512,pending:5512,decisions:0});
  assert.equal(audit.core.evidenceDependency.result,'pass');
  assert.deepEqual(audit.core.evidenceDependency.summary,{inputs:12,changedInputs:9,outputs:443,affectedOutputs:443,runs:1});
  assert.deepEqual({result:audit.core.scenarioTrace.result,rows:audit.core.scenarioTrace.summary.rows,runtimeRows:audit.core.scenarioTrace.summary.runtimeRows,gaps:audit.core.scenarioTrace.summary.gaps,authorityAtomicRows:audit.core.scenarioTrace.summary.authorityAtomicRows,completionEligibleRows:audit.core.scenarioTrace.summary.completionEligibleRows},{result:'pass',rows:290,runtimeRows:16,gaps:274,authorityAtomicRows:0,completionEligibleRows:0});
  assert.equal(audit.core.nonRegression.result,'pass');
  assert.deepEqual(audit.core.evidenceDurability.summary,{status:'passed',artifacts:33,rows:16,variants:16});
  assert.equal(audit.core.definitive.result,'fail');
  assert.deepEqual(audit.gaps.map((gap)=>gap.id),postgresqlLock.requiredGapIds);
  assert.equal(audit.gaps.find((gap)=>gap.id==='scenario-runtime-gaps').count,274);
});

test('Flutter固定commitのCore v2 Schema driftと必須output欠落を保持する',()=>{
  const validated=validateFixedCommitAudit(flutterEnvelope,schema,trusted);
  assert.equal(validated.ok,true,validated.errors.join('; '));
  const audit=projectFixedCommitAudit(flutterEnvelope,validated);
  assert.deepEqual({commit:audit.source.commit,tree:audit.source.tree},{commit:flutterLock.sourceCommit,tree:flutterLock.sourceTree});
  assert.deepEqual({openRequired:audit.manifest.openRequired,inputs:audit.core.evidenceDependency.summary.inputs,outputs:audit.core.evidenceDependency.summary.outputs,missing:audit.core.evidenceDependency.summary.missingRequiredOutputs},{openRequired:2,inputs:19,outputs:742,missing:1});
  assert.deepEqual({anchors:audit.core.authorityBody.summary.candidateAnchors,unclassified:audit.core.authorityBody.summary.unclassified,pending:audit.core.authorityReview.summary.pendingHuman,decisions:audit.core.authorityReview.summary.decisions},{anchors:74,unclassified:74,pending:74,decisions:0});
  for(const gate of ['evidenceDependency','authorityExtraction','authorityBody','authorityReview','definitive','scenarioTrace','nonRegression','evidenceDurability'])assert.equal(audit.core[gate].result,'fail',gate);
  assert.equal(audit.core.scenarioTrace.summary.gaps,531);
  assert.deepEqual(audit.gaps.map((gap)=>gap.id),flutterLock.requiredGapIds);
});

test('RabbitMQ固定commitの自己宣言完成をCore Gate失敗として保持する',()=>{
  const validated=validateFixedCommitAudit(rabbitmqEnvelope,schema,trusted);
  assert.equal(validated.ok,true,validated.errors.join('; '));
  const audit=projectFixedCommitAudit(rabbitmqEnvelope,validated);
  assert.deepEqual({commit:audit.source.commit,tree:audit.source.tree},{commit:rabbitmqLock.sourceCommit,tree:rabbitmqLock.sourceTree});
  assert.deepEqual({openRequired:audit.manifest.openRequired,inputs:audit.core.evidenceDependency.summary.inputs,changed:audit.core.evidenceDependency.summary.changedInputs,outputs:audit.core.evidenceDependency.summary.outputs},{openRequired:203,inputs:14,changed:2,outputs:2397});
  assert.deepEqual({anchors:audit.core.authorityBody.summary.candidateAnchors,unclassified:audit.core.authorityBody.summary.unclassified,pending:audit.core.authorityReview.summary.pendingHuman,decisions:audit.core.authorityReview.summary.decisions},{anchors:1579,unclassified:1579,pending:1579,decisions:0});
  assert.equal(audit.core.definitive.result,'fail');
  assert.equal(audit.core.definitive.summary.declaredCompletionClass,'subject-definitive');
  assert.equal(audit.core.definitive.summary.completionClass,'not-definitive');
  assert.equal(audit.core.scenarioTrace.summary.gaps,925);
  assert.deepEqual(audit.gaps.map((gap)=>gap.id),rabbitmqLock.requiredGapIds);
});

test('Kotlin固定commitの契約passと実行Gapを同時に保持する',()=>{
  const validated=validateFixedCommitAudit(kotlinEnvelope,schema,trusted);
  assert.equal(validated.ok,true,validated.errors.join('; '));
  const audit=projectFixedCommitAudit(kotlinEnvelope,validated);
  assert.deepEqual({commit:audit.source.commit,tree:audit.source.tree},{commit:kotlinLock.sourceCommit,tree:kotlinLock.sourceTree});
  assert.deepEqual({openRequired:audit.manifest.openRequired,inputs:audit.core.evidenceDependency.summary.inputs,changed:audit.core.evidenceDependency.summary.changedInputs,outputs:audit.core.evidenceDependency.summary.outputs},{openRequired:3,inputs:4,changed:4,outputs:777});
  assert.deepEqual({failed:audit.core.authorityExtraction.summary.failed,deferred:audit.core.authorityExtraction.summary.deferredLocators,unclassified:audit.core.authorityBody.summary.unclassified,pending:audit.core.authorityReview.summary.pendingHuman,decisions:audit.core.authorityReview.summary.decisions},{failed:18,deferred:18,unclassified:146402,pending:146402,decisions:0});
  for(const gate of ['evidenceDependency','authorityExtraction','authorityBody','authorityReview','scenarioTrace','nonRegression'])assert.equal(audit.core[gate].result,'pass',gate);
  assert.equal(audit.core.definitive.result,'fail');
  assert.equal(audit.core.definitive.summary.declaredCompletionClass,'subject-definitive');
  assert.equal(audit.core.definitive.summary.completionClass,'not-definitive');
  assert.deepEqual({runtime:audit.core.scenarioTrace.summary.runtimeRows,gaps:audit.core.scenarioTrace.summary.gaps},{runtime:0,gaps:690});
  assert.deepEqual({result:audit.core.evidenceDurability.result,status:audit.core.evidenceDurability.summary.status},{result:'fail',status:'failed'});
  assert.deepEqual(audit.gaps.map((gap)=>gap.id),kotlinLock.requiredGapIds);
});

test('Zero Trustのbounded closureとDefinitive inventory未完了を分離する',()=>{
  const validated=validateFixedCommitAudit(zeroTrustEnvelope,schema,trusted);
  assert.equal(validated.ok,true,validated.errors.join('; '));
  const audit=projectFixedCommitAudit(zeroTrustEnvelope,validated);
  assert.deepEqual({commit:audit.source.commit,tree:audit.source.tree},{commit:zeroTrustLock.sourceCommit,tree:zeroTrustLock.sourceTree});
  assert.deepEqual({boundedOpenRequired:audit.manifest.openRequired,definitiveOpenRequired:audit.core.definitive.summary.openRequired,coreResult:audit.core.definitive.result},{boundedOpenRequired:0,definitiveOpenRequired:91,coreResult:'fail'});
  assert.deepEqual(audit.depthReference.summary,{axes:18,satisfied:1,partial:17,missing:0});
  assert.equal(audit.depthReference.axes.length,18);
  assert.equal(audit.depthReference.axes.filter((axis)=>axis.status!=='satisfied'&&axis.gaps.length>0).length,17);
  assert.deepEqual({unclassified:audit.core.authorityBody.summary.unclassified,pending:audit.core.authorityReview.summary.pendingHuman,decisions:audit.core.authorityReview.summary.decisions},{unclassified:2786,pending:2786,decisions:0});
  assert.deepEqual({result:audit.core.verificationMatrix.result,rows:audit.core.verificationMatrix.summary.rows,closedRows:audit.core.verificationMatrix.summary.closedRows,gapRows:audit.core.verificationMatrix.summary.gapRows,completionEligibleRows:audit.core.verificationMatrix.summary.completionEligibleRows},{result:'pass',rows:910,closedRows:28,gapRows:882,completionEligibleRows:0});
  assert.deepEqual({rows:audit.core.scenarioTrace.summary.rows,runtimeRows:audit.core.scenarioTrace.summary.runtimeRows,variantCells:audit.core.scenarioTrace.summary.variantCells,closedVariantCells:audit.core.scenarioTrace.summary.closedVariantCells,gaps:audit.core.scenarioTrace.summary.gaps},{rows:910,runtimeRows:28,variantCells:1820,closedVariantCells:56,gaps:882});
  assert.deepEqual(audit.gaps.map((gap)=>gap.id),zeroTrustLock.requiredGapIds);
  assert.equal(audit.readOnly,true);
  assert.equal(audit.autoPromotion,false);
});

test('Frontend固定commitのDepth・Authority・Evidence Dependency Gapを保持する',()=>{
  const validated=validateFixedCommitAudit(frontendBehaviorEnvelope,schema,trusted);
  assert.equal(validated.ok,true,validated.errors.join('; '));
  const audit=projectFixedCommitAudit(frontendBehaviorEnvelope,validated);
  assert.deepEqual({commit:audit.source.commit,tree:audit.source.tree},{commit:frontendBehaviorLock.sourceCommit,tree:frontendBehaviorLock.sourceTree});
  assert.deepEqual({status:audit.manifest.status,openRequired:audit.manifest.openRequired},{status:'incomplete',openRequired:85});
  assert.deepEqual({result:audit.core.evidenceDependency.result,missing:audit.core.evidenceDependency.summary.missingRequiredOutputs},{result:'fail',missing:1});
  assert.deepEqual({stale:audit.core.authorityExtraction.summary.staleSources,deferred:audit.core.authorityExtraction.summary.deferredLocators,unclassified:audit.core.authorityBody.summary.unclassified,pending:audit.core.authorityReview.summary.pendingHuman,decisions:audit.core.authorityReview.summary.decisions,packets:audit.core.authorityReview.summary.packets,projections:audit.core.authorityReview.summary.candidateProjections,proposals:audit.core.authorityReview.summary.machineProposals,staleHolds:audit.core.authorityReview.summary.staleHolds},{stale:3,deferred:4,unclassified:15963,pending:15963,decisions:0,packets:80,projections:230,proposals:113,staleHolds:3});
  assert.deepEqual(audit.depthReference.summary,{axes:18,satisfied:1,partial:17,missing:0});
  assert.equal(audit.depthReference.axes.filter((axis)=>axis.status!=='satisfied'&&axis.gaps.length>0).length,17);
  assert.deepEqual({runtime:audit.core.scenarioTrace.summary.runtimeRows,gaps:audit.core.scenarioTrace.summary.gaps},{runtime:0,gaps:850});
  for(const gate of ['evidenceDependency','definitive','scenarioTrace','nonRegression','evidenceDurability'])assert.equal(audit.core[gate].result,'fail',gate);
  assert.deepEqual(audit.gaps.map((gap)=>gap.id),frontendBehaviorLock.requiredGapIds);
  assert.equal(audit.readOnly,true);
  assert.equal(audit.autoPromotion,false);
});

test('bounded open required 0をDefinitive inventory Gapなしで受理しない',()=>{
  const mutated=structuredClone(zeroTrustEnvelope);
  mutated.payload.gaps=mutated.payload.gaps.filter((gap)=>gap.id!=='definitive-inventory-open-required');
  const result=validateFixedCommitAudit(mutated,schema,trusted);
  assert.equal(result.ok,false);
  assert.match(result.errors.join('; '),/Definitive inventory/);
});

test('改変とRelease/Definitiveへの格上げを拒否する',()=>{
  const tampered=structuredClone(envelope);tampered.payload.manifest.openRequired=21;
  assert.equal(validateFixedCommitAudit(tampered,schema,trusted).ok,false);
  const promoted=structuredClone(envelope);promoted.payload.releaseBoundary.signedManifest=true;promoted.payload.manifest.status='complete';promoted.payload.manifest.openRequired=0;promoted.payload.autoPromotion=true;
  const result=validateFixedCommitAudit(promoted,schema,trusted);
  assert.equal(result.ok,false);
  assert.ok(result.errors.some((error)=>error.includes('ReleaseまたはDefinitive')));
  assert.ok(result.errors.some((error)=>error.includes('incomplete境界')));
  assert.ok(result.errors.some((error)=>error.includes('read-only/autoPromotion')));
});
