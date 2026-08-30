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
  assert.equal(audit.core.definitive.result,'fail');
  assert.deepEqual(audit.gaps.map((gap)=>gap.id),postgresqlLock.requiredGapIds);
  assert.equal(audit.gaps.find((gap)=>gap.id==='scenario-runtime-gaps').count,278);
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

test('改変とRelease/Definitiveへの格上げを拒否する',()=>{
  const tampered=structuredClone(envelope);tampered.payload.manifest.openRequired=21;
  assert.equal(validateFixedCommitAudit(tampered,schema,trusted).ok,false);
  const promoted=structuredClone(envelope);promoted.payload.releaseBoundary.signedManifest=true;promoted.payload.manifest.status='complete';promoted.payload.manifest.openRequired=0;promoted.payload.autoPromotion=true;
  const result=validateFixedCommitAudit(promoted,schema,trusted);
  assert.equal(result.ok,false);
  assert.ok(result.errors.some((error)=>error.includes('ReleaseまたはDefinitive')));
  assert.ok(result.errors.some((error)=>error.includes('incomplete/open required')));
  assert.ok(result.errors.some((error)=>error.includes('read-only/autoPromotion')));
});
