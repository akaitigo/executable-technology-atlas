#!/usr/bin/env node
import { mkdir, readFile, rename, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { classifySubjectCompletion, loadTrust, schemaValidators, verifyEnvelope, validateCompletionCertificate, validateRelease } from './lib/validate.mjs';
import { sha256 } from './lib/crypto.mjs';
import { projectDepthReference, validateDepthReference } from './lib/depth-reference.mjs';
import { projectAuthorityReview, validateAuthorityReviewBundle } from './lib/authority-review.mjs';
import { missingEvidenceDependency, projectEvidenceDependency, validateEvidenceDependencyEnvelope } from './lib/evidence-dependency.mjs';
import { missingDefinitiveV2, projectDefinitiveV2, validateDefinitiveV2Envelope } from './lib/definitive-v2.mjs';
import { missingFixedCommitAudit, projectFixedCommitAudit, validateFixedCommitAudit } from './lib/fixed-commit-audit.mjs';
import { neutralizeDisplayText } from './lib/neutral-language.mjs';

const root = process.cwd();
const fixtureRoot = path.resolve(process.argv[2] ?? path.join(root, 'fixtures'));
const output = path.resolve(process.argv[3] ?? path.join(root, 'app', 'data', 'index.generated.json'));
const reportPath = path.resolve(process.argv[4] ?? path.join(root, 'evidence', 'import-report.json'));
const bootstrapPath = path.join(root, 'app', 'data', 'index-bootstrap.generated.json');
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
const fixedCommitAuditSchema=JSON.parse(await readFile(path.join(root,'contracts','schemas','fixed-commit-audit.schema.json'),'utf8'));
const definitiveV2Lock=JSON.parse(await readFile(path.join(root,'contracts','definitive-v2-lock.json'),'utf8'));
const definitiveV2Schemas={};for(const[name,file,digest]of [['definitive','definitive.schema.json',definitiveV2Lock.definitiveSchemaDigest],['certificate','definitive-certificate.schema.json',definitiveV2Lock.certificateSchemaDigest],['migration','definitive-migration.schema.json',definitiveV2Lock.migrationSchemaDigest]]){const bytes=await readFile(path.join(root,'contracts','schemas',file));if(sha256(bytes)!==digest)throw new Error(`Definitive v2 ${name} Schemaが固定Core commitと一致しません`);definitiveV2Schemas[name]=JSON.parse(bytes);}
const evidenceDependencies=new Map();const evidenceDependencyImports=[];
for(const item of registry.evidenceDependencies??[]){const envelope=JSON.parse(await readFile(path.join(fixtureRoot,item.file),'utf8'));const integrity=verifyEnvelope(envelope,trustedKeys);const contract=validateEvidenceDependencyEnvelope(envelope,evidenceDependencyLock,evidenceDependencySchema,integrity);const errors=[...contract.errors];if(item.subjectId!==envelope.payload?.subjectId||item.atlasId!==envelope.payload?.atlasId||item.repository!==envelope.payload?.repository||item.commit!==envelope.payload?.sourceCommit||item.digest!==envelope.release?.digest)errors.push('Evidence Dependency registry bindingがEnvelopeと一致しません');const verification=errors.length===0?'verified':'quarantined';evidenceDependencyImports.push({subjectId:item.subjectId,commit:item.commit,digest:item.digest,verification,errors,graphStatus:contract.graph?.status??null,gateResult:contract.gate?.result??null});if(verification==='verified')evidenceDependencies.set(item.subjectId,projectEvidenceDependency(envelope,contract,integrity));}
const fixedCommitAudits=new Map();const fixedCommitAuditImports=[];
for(const item of registry.fixedCommitAudits??[]){const envelope=JSON.parse(await readFile(path.join(fixtureRoot,item.file),'utf8'));const contract=validateFixedCommitAudit(envelope,fixedCommitAuditSchema,trustedKeys);const errors=[...contract.errors];if(item.subjectId!==envelope.payload?.subjectId||item.atlasId!==envelope.payload?.atlasId||item.repository!==envelope.payload?.repository||item.commit!==envelope.payload?.sourceCommit||item.digest!==envelope.attestation?.digest)errors.push('Fixed commit audit registry bindingがEnvelopeと一致しません');const verification=errors.length===0?'verified':'quarantined';fixedCommitAuditImports.push({subjectId:item.subjectId,commit:item.commit,digest:item.digest,verification,errors,status:verification==='verified'?'fixed-commit-incomplete':'quarantined',gaps:envelope.payload?.gaps?.length??0});if(verification==='verified')fixedCommitAudits.set(item.subjectId,projectFixedCommitAudit(envelope,contract));}
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

const definitiveV2=new Map();const definitiveV2Imports=[];
for(const item of registry.definitiveV2??[]){const envelope=JSON.parse(await readFile(path.join(fixtureRoot,item.file),'utf8'));const integrity=verifyEnvelope(envelope,trustedKeys);const contract=validateDefinitiveV2Envelope(envelope,definitiveV2Lock,definitiveV2Schemas,integrity);const errors=[...contract.errors];const boundRelease=(releaseDetailsByRepository.get(item.repository)??[]).find((release)=>release.digest===envelope.payload?.releaseDigest&&release.commit===envelope.payload?.sourceCommit&&release.atlasId===item.atlasId);if(!boundRelease)errors.push('Definitive v2が検証済み固定Releaseへbindingされていません');if(item.subjectId!==envelope.payload?.subjectId||item.atlasId!==envelope.payload?.atlasId||item.repository!==envelope.payload?.repository||item.commit!==envelope.payload?.sourceCommit||item.digest!==envelope.release?.digest||item.releaseDigest!==envelope.payload?.releaseDigest)errors.push('Definitive v2 registry bindingがEnvelopeと一致しません');const verification=errors.length===0?'verified':'quarantined';definitiveV2Imports.push({subjectId:item.subjectId,commit:item.commit,digest:item.digest,releaseDigest:item.releaseDigest,verification,errors,gateResult:contract.gate?.result??null});if(verification==='verified')definitiveV2.set(item.subjectId,projectDefinitiveV2(envelope,contract,integrity));}

const subjects = [];
for (const domain of catalog.domains) for (const subject of domain.subjects) {
  const depthReference = depthReferences.get(subject.id) ?? null;
  const authorityReview = authorityReviews.get(subject.id) ?? null;
  const evidenceDependency=evidenceDependencies.get(subject.id)??missingEvidenceDependency(subject);
  const fixedCommitAudit=fixedCommitAudits.get(subject.id)??null;
  const fixedCommitAuditIndex=fixedCommitAudit?{schemaVersion:fixedCommitAudit.schemaVersion,subjectId:fixedCommitAudit.subjectId,atlasId:fixedCommitAudit.atlasId,availability:'available',status:fixedCommitAudit.status,source:{repository:fixedCommitAudit.source.repository,commit:fixedCommitAudit.source.commit,tree:fixedCommitAudit.source.tree,attestationDigest:fixedCommitAudit.source.attestationDigest},manifest:{status:fixedCommitAudit.manifest.status,openRequired:fixedCommitAudit.manifest.openRequired},gapCount:fixedCommitAudit.gaps.length,gapIds:fixedCommitAudit.gaps.map((gap)=>gap.id),detailUrl:`/data/fixed-commit-audits/${subject.id}/${fixedCommitAudit.source.attestationDigest.replace(/^sha256:/,'')}.json`,coreGate:{result:fixedCommitAudit.core.definitive.result,command:'atlas audit <fixed-clean-commit> --gate definitive',diagnostics:fixedCommitAudit.core.definitive.diagnostics??[]},readOnly:true,autoPromotion:false}:missingFixedCommitAudit(subject);
  const evidenceDependencyIndex=evidenceDependency.availability==='available'?{...evidenceDependency,inputs:undefined,outputs:undefined,requiredOutputs:undefined,structures:undefined,detailUrl:`/data/evidence-dependencies/${subject.id}.json`}:evidenceDependency;
  const authorityReviewIndex = authorityReview ? { schemaVersion:1, subjectId:authorityReview.subjectId, atlasId:authorityReview.atlasId, status:authorityReview.status, mode:authorityReview.mode, queueId:authorityReview.queueId, summary:authorityReview.summary, capabilities:authorityReview.capabilities, exportUrl:`/data/authority-reviews/${subject.id}/review-export.v1.json`, source:authorityReview.source } : null;
  let releaseHistory = (releasesByRepository.get(subject.repository) ?? []).map((item) => ({ ...item, detailUrl: `/data/releases/${subject.id}/${item.digest.replace(/^sha256:/, '')}.json` }));
  let release = releaseHistory.at(-1) ?? null;
  const definitive=definitiveV2.get(subject.id)??missingDefinitiveV2(subject,release,definitiveV2Lock);
  if(definitive.status==='subject-definitive'&&release?.digest===definitive.source?.releaseDigest){const completion={classification:'subject-definitive',definitive:true,reason:'core-v2-definitive-gate-pass',certificateSchemaVersion:2,corePolicyVersion:'2.0.0',coverageEpoch:release.epoch,trustUsage:definitive.certificate.trust.usage};releaseHistory=releaseHistory.map((item)=>item.digest===release.digest?{...item,completion,definitiveCertificate:definitive.certificate}:item);release=releaseHistory.at(-1);}
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
    fixedCommitAudit:fixedCommitAuditIndex,
    definitiveV2:definitive.availability==='available'?{...definitive,detailUrl:`/data/definitive-v2/${subject.id}.json`}:definitive,
    searchText: [subject.id,subject.title,subject.repository,subject.scope,subject.excludes.join(' '),domain.title,release?.atlasId,release?.skill?.router?.id,release?.outcomes?.join(' '),release?.surfaces?.map((item) => item.id).join(' '),depthReference?.axes.map((axis)=>`${axis.id} ${axis.title} ${axis.denominator}`).join(' '),authorityReview?'authority human review read-only packet projection machine proposal pending reviewed stale hold include exclude merge split defer':'',fixedCommitAudit?`fixed clean commit audit unpublished incomplete ${fixedCommitAudit.source.commit} ${fixedCommitAudit.gaps.map((gap)=>gap.id).join(' ')}`:'fixed clean commit audit input missing not evaluated',`evidence dependency graph ${evidenceDependency.status} input changed current impacted output stale rerun runtime identity missing required output proof closure structure drift core gate`,`definitive v2 ${definitive.status} bounded complete subject definitive authority inventory closure runtime profile gap excluded infeasible unclassified` ].filter(Boolean).join(' ').toLocaleLowerCase('ja'),
  });
}

const definitiveValues=subjects.map((item)=>item.definitiveV2);
const definitiveGapCounts=[...definitiveValues.flatMap((item)=>item.gapIds).reduce((counts,id)=>counts.set(id,(counts.get(id)??0)+1),new Map())].map(([id,count])=>({id,count})).sort((a,b)=>a.id.localeCompare(b.id));
const definitiveRuntimeProfiles=definitiveValues.flatMap((item)=>item.runtimeProfiles);
const index = {
  schemaVersion: 1,
  catalog: { id: catalog.catalog_id, coverageEpoch: catalog.coverage_epoch, scopeStatement: catalog.scope_statement, release: catalogEnvelope.release, signature: catalogEnvelope.signature, trust: catalogVerification.trust, canonical: catalogEnvelope.payload.core },
  generatedAt: catalogEnvelope.release.publishedAt,
  sourcePolicy: 'fixed-release-or-attested-clean-commit-only',
  completionPolicy: { definitiveGate: 'core-v2-final-fail-closed', coreCommit:definitiveV2Lock.coreCommit, boundedCertificateSchemaVersions: [1], definitiveCertificateSchemaVersion:2, autoPromotion: false, requiredForDefinitive: ['public-trust-key','signed-definitive-v2-bundle','core-v2-definitive-gate-pass'] },
  completionSummary: { openRequired: subjects.reduce((sum, subject) => sum + (subject.release?.coverage.openRequired ?? 0), 0), unclassified: subjects.filter((subject) => subject.completion.classification === 'unclassified').length, boundedHistorical: subjects.flatMap((subject) => subject.releaseHistory).filter((release) => release.completion.classification === 'bounded-historical').length, subjectDefinitive: subjects.filter((subject) => subject.completion.definitive).length },
  depthReferenceSummary: { subjects:depthReferences.size, axes:[...depthReferences.values()].reduce((sum,item)=>sum+item.summary.axes,0), satisfied:[...depthReferences.values()].reduce((sum,item)=>sum+item.summary.satisfied,0), partial:[...depthReferences.values()].reduce((sum,item)=>sum+item.summary.partial,0), definitive:0 },
  authorityReviewSummary: { subjects:authorityReviews.size, packets:[...authorityReviews.values()].reduce((sum,item)=>sum+item.summary.packets,0), projections:[...authorityReviews.values()].reduce((sum,item)=>sum+item.summary.candidate_domain_projections,0), machineProposals:[...authorityReviews.values()].reduce((sum,item)=>sum+item.summary.proposed_clusters,0), pendingHuman:[...authorityReviews.values()].reduce((sum,item)=>sum+item.summary.pending_human,0), humanReviewed:[...authorityReviews.values()].reduce((sum,item)=>sum+item.summary.human_reviewed,0), staleHolds:[...authorityReviews.values()].reduce((sum,item)=>sum+item.summary.stale_document_holds,0), decisions:[...authorityReviews.values()].reduce((sum,item)=>sum+item.summary.decisions,0), hasHumanProgress:[...authorityReviews.values()].some((item)=>item.summary.has_human_progress) },
  evidenceDependencySummary:{coreCommit:evidenceDependencyLock.coreCommit,gateAuthority:evidenceDependencyLock.gateAuthority,subjects:subjects.length,available:subjects.filter((item)=>item.evidenceDependency.availability==='available').length,current:subjects.filter((item)=>item.evidenceDependency.status==='current').length,stale:subjects.filter((item)=>item.evidenceDependency.status==='stale-or-incomplete').length,missing:subjects.filter((item)=>item.evidenceDependency.status==='missing-required-output').length,autoPromotion:false},
  fixedCommitAuditSummary:{subjects:subjects.length,available:fixedCommitAudits.size,incomplete:subjects.filter((item)=>item.fixedCommitAudit.status==='fixed-commit-incomplete').length,missing:subjects.filter((item)=>item.fixedCommitAudit.status==='fixed-commit-input-missing').length,releaseEligible:0,gapInstances:[...fixedCommitAudits.values()].reduce((sum,item)=>sum+item.gaps.reduce((count,gap)=>count+gap.count,0),0),inputGapInstances:subjects.filter((item)=>item.fixedCommitAudit.status==='fixed-commit-input-missing').length,readOnly:true,autoPromotion:false},
  definitiveV2Summary:{coreCommit:definitiveV2Lock.coreCommit,contractStatus:'final',subjects:subjects.length,available:definitiveValues.filter((item)=>item.availability==='available').length,definitive:definitiveValues.filter((item)=>item.status==='subject-definitive').length,incomplete:definitiveValues.filter((item)=>item.status==='subject-definitive-incomplete').length,missing:definitiveValues.filter((item)=>item.status==='subject-definitive-input-missing').length,inventoryUnevaluated:definitiveValues.filter((item)=>item.inventoryClosure.status==='not-evaluated').length,openRequiredKnown:definitiveValues.reduce((sum,item)=>sum+(item.inventoryClosure.openRequired??0),0),excluded:definitiveValues.reduce((sum,item)=>sum+item.inventoryClosure.excluded,0),infeasible:definitiveValues.reduce((sum,item)=>sum+item.inventoryClosure.infeasible,0),runtimeProfiles:definitiveRuntimeProfiles.length,runtimeProfilesCurrent:definitiveRuntimeProfiles.filter((item)=>item.status==='current'&&item.runtimeIdentity).length,runtimeProfilesUnverified:definitiveRuntimeProfiles.filter((item)=>item.status!=='current'||!item.runtimeIdentity).length,gapInstances:definitiveGapCounts.reduce((sum,item)=>sum+item.count,0),gapCounts:definitiveGapCounts,autoPromotion:false},
  failureVisibility: { fixtureOnly: failureScenarios.fixtureOnly, scenarios: failureScenarios.scenarios },
  fallback: { strategy: 'last-known-good', message: '新規取込に失敗した場合は最後に検証済みのIndexを維持します。' },
  subjects,
  verification: { verified: imports.filter((item) => item.verification === 'verified').length, quarantined: imports.filter((item) => item.verification === 'quarantined').length, absent: subjects.filter((item) => !item.release).length },
};
index.digest = sha256(JSON.parse(JSON.stringify(index)));
const indexDocument=`${JSON.stringify(index,null,2)}\n`;
const indexArtifactDigest=sha256(Buffer.from(indexDocument));
const publicIndexRelativePath=`public/data/index/${index.digest.replace(/^sha256:/,'')}.json`;
const publicIndexPath=path.join(root,publicIndexRelativePath);
const bootstrap={
  schemaVersion:1,
  generatedAt:index.generatedAt,
  indexDigest:index.digest,
  artifactDigest:indexArtifactDigest,
  publicUrl:`/${publicIndexRelativePath.replace(/^public\//,'')}`,
  subjects:index.subjects.length,
  completionSummary:index.completionSummary,
  definitiveV2Summary:index.definitiveV2Summary,
  evidenceDependencySummary:index.evidenceDependencySummary,
  fixedCommitAuditSummary:index.fixedCommitAuditSummary,
  readOnly:true,
  autoPromotion:false,
  fallback:{status:'index-unavailable-not-evaluated',message:'検証済みIndexを読み込めないため、Subject一覧と完成判定を表示しません。'},
};
await mkdir(path.dirname(reportPath), { recursive: true });
const outputTemporary = `${output}.tmp`;
const reportTemporary = `${reportPath}.tmp`;
const verdict = subjects.length === 97 && imports.every((item) => item.verification === 'verified') && depthImports.length === 1 && depthImports.every((item) => item.verification === 'verified') && reviewImports.length===1 && reviewImports.every((item)=>item.verification==='verified')&&evidenceDependencyImports.every((item)=>item.verification==='verified')&&fixedCommitAuditImports.every((item)=>item.verification==='verified')&&definitiveV2Imports.every((item)=>item.verification==='verified') ? 'pass' : 'fail';
await writeFile(reportTemporary, `${JSON.stringify({ schemaVersion: 1, catalog: catalogVerification, imports, depthImports, reviewImports, evidenceDependencyImports, fixedCommitAuditImports, definitiveV2Imports, index: { path: path.relative(root, output), digest: index.digest, subjects: subjects.length }, verdict }, null, 2)}\n`);
await rename(reportTemporary, reportPath);
if (verdict === 'fail') {
  console.error(`取込失敗: 検証済みIndexと詳細は更新しません / quarantined=${index.verification.quarantined}`);
  process.exitCode = 1;
} else {
  const detailRoot = path.join(root, 'public', 'data', 'releases');
  const fixedAuditRoot=path.join(root,'public','data','fixed-commit-audits');for(const[subjectId,value]of fixedCommitAudits){const subjectRoot=path.join(fixedAuditRoot,subjectId);await mkdir(subjectRoot,{recursive:true});await writeFile(path.join(subjectRoot,`${value.source.attestationDigest.replace(/^sha256:/,'')}.json`),`${JSON.stringify(value,null,2)}\n`);}
  const dependencyRoot=path.join(root,'public','data','evidence-dependencies');await rm(dependencyRoot,{recursive:true,force:true});await mkdir(dependencyRoot,{recursive:true});for(const[subjectId,dependency]of evidenceDependencies)await writeFile(path.join(dependencyRoot,`${subjectId}.json`),`${JSON.stringify(dependency,null,2)}\n`);
  const definitiveRoot=path.join(root,'public','data','definitive-v2');await rm(definitiveRoot,{recursive:true,force:true});await mkdir(definitiveRoot,{recursive:true});for(const[subjectId,value]of definitiveV2)await writeFile(path.join(definitiveRoot,`${subjectId}.json`),`${JSON.stringify(value,null,2)}\n`);
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
  await mkdir(path.dirname(publicIndexPath),{recursive:true});
  const publicIndexTemporary=`${publicIndexPath}.tmp`;
  await writeFile(publicIndexTemporary,indexDocument);
  await rename(publicIndexTemporary,publicIndexPath);
  await writeFile(outputTemporary,indexDocument);
  await rename(outputTemporary, output);
  const bootstrapTemporary=`${bootstrapPath}.tmp`;
  await writeFile(bootstrapTemporary,`${JSON.stringify(bootstrap,null,2)}\n`);
  await rename(bootstrapTemporary,bootstrapPath);
  console.log(`Index生成済み: ${subjects.length} subjects / verified=${index.verification.verified} / absent=${index.verification.absent} / quarantined=${index.verification.quarantined}`);
}
