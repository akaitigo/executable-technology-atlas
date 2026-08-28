#!/usr/bin/env node
import { mkdir, readFile, rename, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { classifySubjectCompletion, loadTrust, schemaValidators, verifyEnvelope, validateCompletionCertificate, validateRelease } from './lib/validate.mjs';
import { sha256 } from './lib/crypto.mjs';
import { projectDepthReference, validateDepthReference } from './lib/depth-reference.mjs';
import { projectAuthorityReview, validateAuthorityReviewBundle } from './lib/authority-review.mjs';
import { missingEvidenceDependency, projectEvidenceDependency, validateEvidenceDependencyEnvelope } from './lib/evidence-dependency.mjs';
import { neutralizeDisplayText } from './lib/neutral-language.mjs';

const root = process.cwd();
const fixtureRoot = path.resolve(process.argv[2] ?? path.join(root, 'fixtures'));
const output = path.resolve(process.argv[3] ?? path.join(root, 'app', 'data', 'index.generated.json'));
const reportPath = path.resolve(process.argv[4] ?? path.join(root, 'evidence', 'import-report.json'));
const trustedKeys = await loadTrust(fixtureRoot);
const validators = await schemaValidators(path.join(root, 'contracts', 'schemas'));

const catalogEnvelope = JSON.parse(await readFile(path.join(fixtureRoot, 'core', 'catalog.release.json'), 'utf8'));
const catalogVerification = verifyEnvelope(catalogEnvelope, trustedKeys);
if (!catalogVerification.ok) throw new Error(`Catalog検証失敗: ${catalogVerification.errors.join(', ')}`);
const catalog = catalogEnvelope.payload.catalog;
if (!validators.catalog(catalog)) throw new Error(`Catalog Schema不適合: ${JSON.stringify(validators.catalog.errors)}`);

const registry = JSON.parse(await readFile(path.join(fixtureRoot, 'registry.json'), 'utf8'));
const failureScenarios = JSON.parse(await readFile(path.join(fixtureRoot, 'failure-scenarios.json'), 'utf8'));
const evidenceDependencyLock=JSON.parse(await readFile(path.join(root,'contracts','evidence-dependency-lock.json'),'utf8'));
const evidenceDependencySchemaBytes=await readFile(path.join(root,'contracts','schemas','evidence-dependency-graph.schema.json'));
if(sha256(evidenceDependencySchemaBytes)!==evidenceDependencyLock.schemaDigest)throw new Error('Evidence Dependency Graph Schemaが固定Core commitと一致しません');
const evidenceDependencyDocumentBytes=await readFile(path.join(root,evidenceDependencyLock.vendoredContractDocumentPath));
if(sha256(evidenceDependencyDocumentBytes)!==evidenceDependencyLock.contractDocumentDigest)throw new Error('Evidence Dependency Graph契約文書が固定Core commitと一致しません');
const evidenceDependencySchema=JSON.parse(evidenceDependencySchemaBytes);
const evidenceDependencies=new Map();const evidenceDependencyImports=[];
for(const item of registry.evidenceDependencies??[]){const envelope=JSON.parse(await readFile(path.join(fixtureRoot,item.file),'utf8'));const integrity=verifyEnvelope(envelope,trustedKeys);const contract=validateEvidenceDependencyEnvelope(envelope,evidenceDependencyLock,evidenceDependencySchema,integrity);const errors=[...contract.errors];if(item.subjectId!==envelope.payload?.subjectId||item.atlasId!==envelope.payload?.atlasId||item.repository!==envelope.payload?.repository||item.commit!==envelope.payload?.sourceCommit||item.digest!==envelope.release?.digest)errors.push('Evidence Dependency registry bindingがEnvelopeと一致しません');const verification=errors.length===0?'verified':'quarantined';evidenceDependencyImports.push({subjectId:item.subjectId,commit:item.commit,digest:item.digest,verification,errors,graphStatus:contract.graph?.status??null,gateResult:contract.gate?.result??null});if(verification==='verified')evidenceDependencies.set(item.subjectId,projectEvidenceDependency(envelope,contract,integrity));}
const depthReferenceLock = JSON.parse(await readFile(path.join(root, 'contracts', 'depth-reference-lock.json'), 'utf8'));
const depthReferences = new Map();
const depthImports = [];
for (const item of registry.depthReferences ?? []) {
  const envelope = JSON.parse(await readFile(path.join(fixtureRoot, item.file), 'utf8'));
  const integrity = verifyEnvelope(envelope, trustedKeys);
  const contract = validateDepthReference(envelope, depthReferenceLock, integrity);
  const errors = [...contract.errors];
  if (item.subjectId !== envelope.release?.subjectId || item.atlasId !== envelope.release?.atlasId || item.repository !== envelope.release?.repository || item.commit !== envelope.release?.commit || item.digest !== envelope.release?.digest || item.sourceDigest !== envelope.source?.digest) errors.push('Depth Reference registry bindingがEnvelopeと一致しません');
  const verification = errors.length === 0 ? 'verified' : 'quarantined';
  depthImports.push({ subjectId:item.subjectId, commit:item.commit, digest:item.digest, verification, errors, axes:contract.axes, counts:contract.counts });
  if (verification === 'verified') depthReferences.set(item.subjectId, projectDepthReference(envelope, integrity));
}
const authorityReviewLock = JSON.parse(await readFile(path.join(root, 'contracts', 'authority-review-lock.json'), 'utf8'));
const authorityReviews = new Map();
const authorityReviewBundles = new Map();
const reviewImports = [];
for (const item of registry.authorityReviews ?? []) {
  const envelope = JSON.parse(await readFile(path.join(fixtureRoot,item.envelopeFile),'utf8'));
  const archiveBytes = await readFile(path.join(fixtureRoot,item.archiveFile));
  const integrity = verifyEnvelope(envelope,trustedKeys);
  const contract = validateAuthorityReviewBundle(envelope,archiveBytes,authorityReviewLock,integrity);
  const errors=[...contract.errors];
  if(item.subjectId!==envelope.payload?.subjectId||item.atlasId!==envelope.payload?.atlasId||item.repository!==envelope.payload?.repository||item.commit!==envelope.payload?.sourceCommit||item.digest!==envelope.release?.digest||item.archiveDigest!==envelope.payload?.archiveDigest)errors.push('Authority Review registry bindingがEnvelopeと一致しません');
  const verification=errors.length===0?'verified':'quarantined';
  reviewImports.push({subjectId:item.subjectId,commit:item.commit,digest:item.digest,verification,errors,summary:contract.archive?.reviewExport?.summary??null,progress:contract.progress??null});
  if(verification==='verified'){authorityReviews.set(item.subjectId,projectAuthorityReview(envelope,contract,integrity));authorityReviewBundles.set(item.subjectId,contract.archive);}
}
const releasesByRepository = new Map();
const releaseDetailsByRepository = new Map();
const imports = [];
for (const item of registry.releases) {
  const absolute = path.join(fixtureRoot, item.file);
  const envelope = JSON.parse(await readFile(absolute, 'utf8'));
  const integrity = verifyEnvelope(envelope, trustedKeys);
  const certificateVerification = integrity.ok ? validateCompletionCertificate(envelope.payload, validators, envelope.release) : { present: Boolean(envelope.payload.certificate), ok: false, errors: [] };
  const contract = integrity.ok ? validateRelease(envelope.payload, validators, envelope.release) : { ok: false, errors: [] };
  const errors = [...integrity.errors, ...contract.errors];
  const verification = errors.length === 0 ? 'verified' : 'quarantined';
  const coverage = envelope.payload.coverage?.targets ?? [];
  const required = coverage.filter((target) => target.requirement === 'required');
  const closedRequired = required.filter((target) => ['covered','excluded','infeasible'].includes(target.state));
  const evidenceIds = new Set((envelope.payload.evidence ?? []).map((item) => item.id));
  const unresolvedCoveredEvidence = coverage.filter((target) => target.state === 'covered' && !(target.evidence_ids ?? []).every((id) => evidenceIds.has(id))).length;
  const completion = classifySubjectCompletion(envelope.payload, certificateVerification, integrity.trust);
  const observedProfiles = [...new Set((envelope.payload.evidence ?? []).map((record) => record.environment?.profile).filter(Boolean))].sort();
  const release = {
    atlasId: envelope.payload.atlas?.id,
    version: envelope.release?.version,
    status: envelope.payload.atlas?.status,
    epoch: envelope.payload.atlas?.coverage?.epoch,
    corePolicyVersion: envelope.payload.atlas?.completion?.policy_version,
    commit: envelope.release?.commit,
    uri: envelope.release?.uri,
    digest: envelope.release?.digest,
    signature: envelope.signature,
    trust: integrity.trust,
    verification,
    verificationErrors: errors,
    authorityLockDigest: envelope.payload.coverage?.authority_lock_digest,
    requiredProfiles: envelope.payload.atlas?.completion?.required_profiles ?? [],
    observedProfiles,
    scope: envelope.payload.atlas?.scope,
    audiences: envelope.payload.mastery?.audiences ?? [],
    outcomes: envelope.payload.mastery?.outcomes?.map((item) => item.id) ?? [],
    surfaces: envelope.payload.mastery?.surfaces?.map((item) => ({ id: item.id, applicability: item.applicability })) ?? [],
    coverage: { required: required.length, closed: closedRequired.length, openRequired: required.length - closedRequired.length, percent: required.length ? Math.round((closedRequired.length / required.length) * 100) : 0, unresolvedCoveredEvidence, states: Object.fromEntries(['missing','planned','partial','covered','excluded','infeasible','expired'].map((state) => [state, coverage.filter((target) => target.state === state).length])) },
    targets: coverage,
    evidence: envelope.payload.evidence ?? [],
    skill: envelope.payload.skillPackage,
    certificate: envelope.payload.certificate,
    certificateVerification: { present: certificateVerification.present, status: certificateVerification.present ? certificateVerification.ok ? 'verified' : 'invalid' : 'absent', digest: certificateVerification.digest ?? null },
    completion,
  };
  imports.push({ atlasId: release.atlasId, version: release.version, verification, errors, digest: release.digest, completion });
  if (verification === 'verified') {
    const details = releaseDetailsByRepository.get(item.repository) ?? [];
    details.push(release);
    releaseDetailsByRepository.set(item.repository, details);
    const summary = Object.fromEntries(Object.entries(release).filter(([key]) => !['targets', 'evidence'].includes(key)));
    const releases = releasesByRepository.get(item.repository) ?? [];
    releases.push({ ...summary, evidenceCount: release.evidence.length });
    releasesByRepository.set(item.repository, releases);
  }
}

const subjects = [];
for (const domain of catalog.domains) for (const subject of domain.subjects) {
  const depthReference = depthReferences.get(subject.id) ?? null;
  const authorityReview = authorityReviews.get(subject.id) ?? null;
  const evidenceDependency=evidenceDependencies.get(subject.id)??missingEvidenceDependency(subject);
  const evidenceDependencyIndex=evidenceDependency.availability==='available'?{...evidenceDependency,inputs:undefined,outputs:undefined,requiredOutputs:undefined,structures:undefined,detailUrl:`/data/evidence-dependencies/${subject.id}.json`}:evidenceDependency;
  const authorityReviewIndex = authorityReview ? { schemaVersion:1, subjectId:authorityReview.subjectId, atlasId:authorityReview.atlasId, status:authorityReview.status, mode:authorityReview.mode, queueId:authorityReview.queueId, summary:authorityReview.summary, capabilities:authorityReview.capabilities, exportUrl:`/data/authority-reviews/${subject.id}/review-export.v1.json`, source:authorityReview.source } : null;
  const releaseHistory = (releasesByRepository.get(subject.repository) ?? []).map((item) => ({ ...item, detailUrl: `/data/releases/${subject.id}/${item.digest.replace(/^sha256:/, '')}.json` }));
  const release = releaseHistory.at(-1) ?? null;
  subjects.push({
    ...subject,
    domain: { id: domain.id, title: domain.title },
    release,
    releaseHistory,
    currentReleaseDigest: release?.digest ?? null,
    completion: release?.completion ?? { classification: 'unclassified', definitive: false, reason: 'fixed-release-absent', certificateSchemaVersion: null, corePolicyVersion: null, coverageEpoch: null, trustUsage: 'unclassified' },
    depthReference: depthReference ? { ...depthReference, axes:undefined } : null,
    authorityReview:authorityReviewIndex,
    evidenceDependency:evidenceDependencyIndex,
    searchText: [subject.id,subject.title,subject.repository,subject.scope,subject.excludes.join(' '),domain.title,release?.atlasId,release?.skill?.router?.id,release?.outcomes?.join(' '),release?.surfaces?.map((item) => item.id).join(' '),depthReference?.axes.map((axis)=>`${axis.id} ${axis.title} ${axis.denominator}`).join(' '),authorityReview?'authority human review read-only packet projection machine proposal pending reviewed stale hold include exclude merge split defer':'',`evidence dependency graph ${evidenceDependency.status} input changed current impacted output stale rerun runtime identity missing required output proof closure structure drift core gate` ].filter(Boolean).join(' ').toLocaleLowerCase('ja'),
  });
}

const index = {
  schemaVersion: 1,
  catalog: { id: catalog.catalog_id, coverageEpoch: catalog.coverage_epoch, scopeStatement: catalog.scope_statement, release: catalogEnvelope.release, signature: catalogEnvelope.signature, trust: catalogVerification.trust, canonical: catalogEnvelope.payload.core },
  generatedAt: catalogEnvelope.release.publishedAt,
  sourcePolicy: 'fixed-release-only',
  completionPolicy: { definitiveGate: 'pending-core-v2', boundedCertificateSchemaVersions: [1], autoPromotion: false, requiredForDefinitive: ['public-trust-key','core-v2-definitive-certificate'] },
  completionSummary: { openRequired: subjects.reduce((sum, subject) => sum + (subject.release?.coverage.openRequired ?? 0), 0), unclassified: subjects.filter((subject) => subject.completion.classification === 'unclassified').length, boundedHistorical: subjects.flatMap((subject) => subject.releaseHistory).filter((release) => release.completion.classification === 'bounded-historical').length, subjectDefinitive: subjects.filter((subject) => subject.completion.definitive).length },
  depthReferenceSummary: { subjects:depthReferences.size, axes:[...depthReferences.values()].reduce((sum,item)=>sum+item.summary.axes,0), satisfied:[...depthReferences.values()].reduce((sum,item)=>sum+item.summary.satisfied,0), partial:[...depthReferences.values()].reduce((sum,item)=>sum+item.summary.partial,0), definitive:0 },
  authorityReviewSummary: { subjects:authorityReviews.size, packets:[...authorityReviews.values()].reduce((sum,item)=>sum+item.summary.packets,0), projections:[...authorityReviews.values()].reduce((sum,item)=>sum+item.summary.candidate_domain_projections,0), machineProposals:[...authorityReviews.values()].reduce((sum,item)=>sum+item.summary.proposed_clusters,0), pendingHuman:[...authorityReviews.values()].reduce((sum,item)=>sum+item.summary.pending_human,0), humanReviewed:[...authorityReviews.values()].reduce((sum,item)=>sum+item.summary.human_reviewed,0), staleHolds:[...authorityReviews.values()].reduce((sum,item)=>sum+item.summary.stale_document_holds,0), decisions:[...authorityReviews.values()].reduce((sum,item)=>sum+item.summary.decisions,0), hasHumanProgress:[...authorityReviews.values()].some((item)=>item.summary.has_human_progress) },
  evidenceDependencySummary:{coreCommit:evidenceDependencyLock.coreCommit,gateAuthority:evidenceDependencyLock.gateAuthority,subjects:subjects.length,available:subjects.filter((item)=>item.evidenceDependency.availability==='available').length,current:subjects.filter((item)=>item.evidenceDependency.status==='current').length,stale:subjects.filter((item)=>item.evidenceDependency.status==='stale-or-incomplete').length,missing:subjects.filter((item)=>item.evidenceDependency.status==='missing-required-output').length,autoPromotion:false},
  failureVisibility: { fixtureOnly: failureScenarios.fixtureOnly, scenarios: failureScenarios.scenarios },
  fallback: { strategy: 'last-known-good', message: '新規取込に失敗した場合は最後に検証済みのIndexを維持します。' },
  subjects,
  verification: { verified: imports.filter((item) => item.verification === 'verified').length, quarantined: imports.filter((item) => item.verification === 'quarantined').length, absent: subjects.filter((item) => !item.release).length },
};
index.digest = sha256(index);
await mkdir(path.dirname(reportPath), { recursive: true });
const outputTemporary = `${output}.tmp`;
const reportTemporary = `${reportPath}.tmp`;
const verdict = subjects.length === 97 && imports.every((item) => item.verification === 'verified') && depthImports.length === 1 && depthImports.every((item) => item.verification === 'verified') && reviewImports.length===1 && reviewImports.every((item)=>item.verification==='verified')&&evidenceDependencyImports.every((item)=>item.verification==='verified') ? 'pass' : 'fail';
await writeFile(reportTemporary, `${JSON.stringify({ schemaVersion: 1, catalog: catalogVerification, imports, depthImports, reviewImports, evidenceDependencyImports, index: { path: path.relative(root, output), digest: index.digest, subjects: subjects.length }, verdict }, null, 2)}\n`);
await rename(reportTemporary, reportPath);
if (verdict === 'fail') {
  console.error(`取込失敗: 検証済みIndexと詳細は更新しません / quarantined=${index.verification.quarantined}`);
  process.exitCode = 1;
} else {
  const detailRoot = path.join(root, 'public', 'data', 'releases');
  const dependencyRoot=path.join(root,'public','data','evidence-dependencies');await rm(dependencyRoot,{recursive:true,force:true});await mkdir(dependencyRoot,{recursive:true});for(const[subjectId,dependency]of evidenceDependencies)await writeFile(path.join(dependencyRoot,`${subjectId}.json`),`${JSON.stringify(dependency,null,2)}\n`);
  for(const [subjectId,bundle]of authorityReviewBundles){const reviewRoot=path.join(root,'public','data','authority-reviews',subjectId);const packetRoot=path.join(reviewRoot,'packets');await rm(reviewRoot,{recursive:true,force:true});await mkdir(packetRoot,{recursive:true});await writeFile(path.join(reviewRoot,'review-export.v1.json'),bundle.exportBytes);for(const entry of bundle.packets)await writeFile(path.join(packetRoot,`${entry.value.packet_id}.json`),entry.bytes);}
  for (const [repository, details] of releaseDetailsByRepository) {
    const subject = subjects.find((item) => item.repository === repository);
    if (!subject) continue;
    const subjectDetailRoot = path.join(detailRoot, subject.id);
    await mkdir(subjectDetailRoot, { recursive: true });
    for (const detail of details) {
      const contentId = detail.digest.replace(/^sha256:/, '');
      const subjectDepthReference = depthReferences.get(subject.id);
      const sourceDetail = { ...detail, ...(subjectDepthReference ? { depthReference:subjectDepthReference } : {}), detailUrl: `/data/releases/${subject.id}/${contentId}.json` };
      const projectedDetail = neutralizeDisplayText(sourceDetail);
      const transformations = JSON.stringify(projectedDetail) === JSON.stringify(sourceDetail) ? [] : ['definitive-marketing-to-neutral-fact'];
      await writeFile(path.join(subjectDetailRoot, `${contentId}.json`), `${JSON.stringify({ ...projectedDetail, displayProjection: { sourceReleaseDigest:detail.digest, transformations } }, null, 2)}\n`);
    }
  }
  await mkdir(path.dirname(output), { recursive: true });
  await writeFile(outputTemporary, `${JSON.stringify(index, null, 2)}\n`);
  await rename(outputTemporary, output);
  console.log(`Index生成済み: ${subjects.length} subjects / verified=${index.verification.verified} / absent=${index.verification.absent} / quarantined=${index.verification.quarantined}`);
}
