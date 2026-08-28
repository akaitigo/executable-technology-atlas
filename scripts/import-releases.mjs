#!/usr/bin/env node
import { mkdir, readFile, rename, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { loadTrust, schemaValidators, verifyEnvelope, validateCompletionCertificate, validateRelease } from './lib/validate.mjs';
import { sha256 } from './lib/crypto.mjs';

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
    scope: envelope.payload.atlas?.scope,
    audiences: envelope.payload.mastery?.audiences ?? [],
    outcomes: envelope.payload.mastery?.outcomes?.map((item) => item.id) ?? [],
    surfaces: envelope.payload.mastery?.surfaces?.map((item) => ({ id: item.id, applicability: item.applicability })) ?? [],
    coverage: { required: required.length, closed: closedRequired.length, percent: required.length ? Math.round((closedRequired.length / required.length) * 100) : 0, unresolvedCoveredEvidence, states: Object.fromEntries(['missing','planned','partial','covered','excluded','infeasible','expired'].map((state) => [state, coverage.filter((target) => target.state === state).length])) },
    targets: coverage,
    evidence: envelope.payload.evidence ?? [],
    skill: envelope.payload.skillPackage,
    certificate: envelope.payload.certificate,
    certificateVerification: { present: certificateVerification.present, status: certificateVerification.present ? certificateVerification.ok ? 'verified' : 'invalid' : 'absent', digest: certificateVerification.digest ?? null },
  };
  imports.push({ atlasId: release.atlasId, version: release.version, verification, errors, digest: release.digest });
  if (verification === 'verified') {
    releaseDetailsByRepository.set(item.repository, release);
    const summary = Object.fromEntries(Object.entries(release).filter(([key]) => !['targets', 'evidence'].includes(key)));
    releasesByRepository.set(item.repository, { ...summary, evidenceCount: release.evidence.length });
  }
}

const subjects = [];
for (const domain of catalog.domains) for (const subject of domain.subjects) {
  const release = releasesByRepository.get(subject.repository) ?? null;
  subjects.push({
    ...subject,
    domain: { id: domain.id, title: domain.title },
    release,
    searchText: [subject.id,subject.title,subject.repository,subject.scope,subject.excludes.join(' '),domain.title,release?.atlasId,release?.skill?.router?.id,release?.outcomes?.join(' '),release?.surfaces?.map((item) => item.id).join(' ')].filter(Boolean).join(' ').toLocaleLowerCase('ja'),
  });
}

const index = {
  schemaVersion: 1,
  catalog: { id: catalog.catalog_id, coverageEpoch: catalog.coverage_epoch, scopeStatement: catalog.scope_statement, release: catalogEnvelope.release, signature: catalogEnvelope.signature, trust: catalogVerification.trust, canonical: catalogEnvelope.payload.core },
  generatedAt: catalogEnvelope.release.publishedAt,
  sourcePolicy: 'fixed-release-only',
  fallback: { strategy: 'last-known-good', message: '新規取込に失敗した場合は最後に検証済みのIndexを維持します。' },
  subjects,
  verification: { verified: imports.filter((item) => item.verification === 'verified').length, quarantined: imports.filter((item) => item.verification === 'quarantined').length, absent: subjects.filter((item) => !item.release).length },
};
index.digest = sha256(index);
await mkdir(path.dirname(output), { recursive: true });
await mkdir(path.dirname(reportPath), { recursive: true });
const detailRoot = path.join(root, 'public', 'data', 'releases');
await mkdir(detailRoot, { recursive: true });
for (const subject of subjects) {
  const detail = releaseDetailsByRepository.get(subject.repository);
  if (detail) await writeFile(path.join(detailRoot, `${subject.id}.json`), `${JSON.stringify(detail, null, 2)}\n`);
}
const outputTemporary = `${output}.tmp`;
const reportTemporary = `${reportPath}.tmp`;
await writeFile(outputTemporary, `${JSON.stringify(index, null, 2)}\n`);
await writeFile(reportTemporary, `${JSON.stringify({ schemaVersion: 1, catalog: catalogVerification, imports, index: { path: path.relative(root, output), digest: index.digest, subjects: subjects.length }, verdict: subjects.length === 97 && imports.every((item) => item.verification === 'verified') ? 'pass' : 'fail' }, null, 2)}\n`);
await rename(outputTemporary, output);
await rename(reportTemporary, reportPath);
console.log(`Index生成済み: ${subjects.length} subjects / verified=${index.verification.verified} / absent=${index.verification.absent} / quarantined=${index.verification.quarantined}`);
if (subjects.length !== 97 || imports.some((item) => item.verification !== 'verified')) process.exitCode = 1;
