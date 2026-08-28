import { createPublicKey } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { sha256, verifyDigest } from './crypto.mjs';

export const OUTCOMES = ['understand','choose','build','verify','operate','troubleshoot','evolve','delegate'];
export const SURFACES = ['orientation-scope','foundations-mechanics','architecture-design','implementation-construction','testing-verification','failure-recovery','operations-observability','security-privacy-safety','performance-capacity-cost','compatibility-integration','migration-evolution-deprecation','decision-comparison','provenance-rights','agent-skill'];

export async function loadTrust(fixtureRoot) {
  const trust = JSON.parse(await readFile(path.join(fixtureRoot, 'trust.json'), 'utf8'));
  return new Map(trust.keys.map((key) => [key.keyId, { publicKey: createPublicKey(key.publicKeyPem), usage: key.usage ?? 'unclassified' }]));
}

export function verifyEnvelope(envelope, trustedKeys) {
  const errors = [];
  if (envelope.schemaVersion !== 1) errors.push('未対応のEnvelope Schemaです');
  const digest = sha256(envelope.payload);
  if (digest !== envelope.release?.digest) errors.push('Release digestが一致しません');
  const trust = trustedKeys.get(envelope.signature?.keyId);
  const publicKey = trust?.publicKey ?? trust;
  if (!publicKey) errors.push('署名鍵がTrust Storeにありません');
  else if (!verifyDigest(envelope.release.digest, envelope.signature.value, publicKey)) errors.push('Ed25519署名が不正です');
  return { ok: errors.length === 0, digest, errors, trust: { keyId: envelope.signature?.keyId ?? null, usage: trust?.usage ?? 'unclassified' } };
}

export async function schemaValidators(contractRoot) {
  const ajv = new Ajv2020({ allErrors: true, strict: false });
  addFormats(ajv);
  const names = ['atlas', 'mastery', 'coverage', 'sources-lock', 'skill-package', 'evidence', 'catalog', 'claim', 'completion-certificate', 'provenance', 'skill-eval', 'third-party'];
  const validators = {};
  for (const name of names) {
    const schema = JSON.parse(await readFile(path.join(contractRoot, `${name}.schema.json`), 'utf8'));
    validators[name] = ajv.compile(schema);
  }
  return validators;
}

export function validateCompletionCertificate(payload, validators, release = {}) {
  const certificate = payload.certificate;
  if (!certificate) return { present: false, ok: payload.atlas?.status !== 'complete', errors: payload.atlas?.status === 'complete' ? ['complete ReleaseにCompletion Certificateがありません'] : [] };
  const errors = [];
  if (!validators['completion-certificate'](certificate)) errors.push(`Completion Certificate: ${validators['completion-certificate'].errors?.map((error) => error.instancePath + ' ' + error.message).join('; ')}`);
  const { signature, ...certificatePayload } = certificate;
  if (sha256(certificatePayload) !== signature?.digest) errors.push('Completion Certificate payload digestが一致しません');
  const expected = {
    atlas_id: payload.atlas?.id,
    atlas_release: payload.skillPackage?.atlas_release,
    coverage_epoch: payload.atlas?.coverage?.epoch,
    authority_lock_digest: payload.coverage?.authority_lock_digest,
    core_policy_version: payload.atlas?.completion?.policy_version,
  };
  for (const [key, value] of Object.entries(expected)) if (certificate[key] !== value) errors.push(`Completion Certificate ${key}がManifestと一致しません`);
  if (release.atlasId && release.atlasId !== payload.atlas?.id) errors.push('Release Atlas IDがManifestと一致しません');
  if (release.version && release.version !== payload.skillPackage?.atlas_release) errors.push('Release VersionがSkill Packageと一致しません');
  const evidence = new Map((payload.evidence ?? []).map((item) => [item.id, item]));
  const profiles = new Map((certificate.required_profiles ?? []).map((item) => [item.profile, item]));
  for (const required of payload.atlas?.completion?.required_profiles ?? []) {
    const profile = profiles.get(required);
    if (!profile || profile.result !== 'pass') errors.push(`Completion Certificateの必須Profile ${required}がpassではありません`);
    for (const evidenceId of profile?.evidence_ids ?? []) {
      const record = evidence.get(evidenceId);
      if (!record || record.verdict !== 'pass' || record.environment?.profile !== required) errors.push(`Completion CertificateのEvidence ${evidenceId}を${required}のpassとして検証できません`);
    }
  }
  if ((certificate.skill_eval?.pass_rate ?? 0) < (payload.skillPackage?.evals?.minimum_pass_rate ?? 1)) errors.push('Completion CertificateのSkill Evalが必要成功率未満です');
  return { present: true, ok: errors.length === 0, errors, digest: signature?.digest ?? null };
}

// Core v1 certificates prove closure only for their fixed historical epoch. They
// do not contain the identity, inventory and public-trust bindings required by
// the forthcoming Definitive Gate v2. Keep this decision fail-closed and in one
// place so a future v2 adapter can replace it only after the canonical contract
// and migration are committed in reference-atlas-core.
export function classifySubjectCompletion(payload, certificateVerification, trust = {}) {
  const certificate = payload.certificate;
  if (certificateVerification?.ok && certificate?.schema_version === 1) {
    return {
      classification: 'bounded-historical',
      definitive: false,
      reason: 'core-v1-fixed-epoch-certificate',
      certificateSchemaVersion: 1,
      corePolicyVersion: certificate.core_policy_version ?? null,
      coverageEpoch: certificate.coverage_epoch ?? null,
      trustUsage: trust.usage ?? 'unclassified',
    };
  }
  return {
    classification: 'not-definitive',
    definitive: false,
    reason: certificate ? 'certificate-not-accepted-as-definitive' : 'certificate-absent',
    certificateSchemaVersion: certificate?.schema_version ?? null,
    corePolicyVersion: certificate?.core_policy_version ?? payload.atlas?.completion?.policy_version ?? null,
    coverageEpoch: certificate?.coverage_epoch ?? payload.atlas?.coverage?.epoch ?? null,
    trustUsage: trust.usage ?? 'unclassified',
  };
}

export function validateRelease(payload, validators, release = {}) {
  const errors = [];
  const docs = [['atlas',payload.atlas],['mastery',payload.mastery],['coverage',payload.coverage],['sources-lock',payload.sources],['skill-package',payload.skillPackage]];
  for (const [name, doc] of docs) if (!validators[name](doc)) errors.push(`${name}: ${validators[name].errors?.map((error) => error.instancePath + ' ' + error.message).join('; ')}`);
  for (const evidence of payload.evidence ?? []) if (!validators.evidence(evidence)) errors.push(`evidence ${evidence?.id ?? '(unknown)'}: schema不適合`);
  const id = payload.atlas?.id;
  for (const [name, doc] of docs.slice(1)) if (doc?.atlas_id !== id) errors.push(`${name}: atlas_id不一致`);
  const epoch = payload.atlas?.coverage?.epoch;
  for (const [name, doc] of [['mastery',payload.mastery],['coverage',payload.coverage],['sources',payload.sources]]) if (doc?.epoch !== epoch) errors.push(`${name}: Coverage Epoch不一致`);
  if (payload.atlas?.skills?.router?.id !== payload.skillPackage?.router?.id || payload.atlas?.skills?.router?.path !== payload.skillPackage?.router?.path) errors.push('Router IDまたはPath不一致');
  const sets = new Set((payload.coverage?.target_sets ?? []).map((item) => item.id));
  for (const item of [...(payload.mastery?.outcomes ?? []), ...(payload.mastery?.surfaces ?? [])]) for (const set of item.target_sets ?? []) if (!sets.has(set)) errors.push(`未定義Target Set参照: ${set}`);
  if (!OUTCOMES.every((idValue) => payload.mastery?.outcomes?.some((item) => item.id === idValue))) errors.push('8 Outcomeが揃っていません');
  if (!SURFACES.every((idValue) => payload.mastery?.surfaces?.some((item) => item.id === idValue))) errors.push('14 Surfaceが揃っていません');
  const targets = payload.coverage?.targets ?? [];
  if (payload.atlas?.status === 'complete') {
    const evidenceIds = new Set((payload.evidence ?? []).map((item) => item.id));
    for (const target of targets.filter((item) => item.state === 'covered')) if (!(target.evidence_ids ?? []).length || !target.evidence_ids.every((idValue) => evidenceIds.has(idValue))) errors.push(`complete Releaseのcovered Target ${target.id}のEvidence参照を検証できません`);
    const openRequired = targets.filter((target) => target.requirement === 'required' && !['covered','excluded','infeasible'].includes(target.state));
    if (openRequired.length) errors.push(`complete Releaseに未Closureの必須Targetが${openRequired.length}件あります`);
  }
  errors.push(...validateCompletionCertificate(payload, validators, release).errors);
  return { ok: errors.length === 0, errors };
}
