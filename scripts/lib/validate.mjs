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
  return new Map(trust.keys.map((key) => [key.keyId, createPublicKey(key.publicKeyPem)]));
}

export function verifyEnvelope(envelope, trustedKeys) {
  const errors = [];
  if (envelope.schemaVersion !== 1) errors.push('未対応のEnvelope Schemaです');
  const digest = sha256(envelope.payload);
  if (digest !== envelope.release?.digest) errors.push('Release digestが一致しません');
  const key = trustedKeys.get(envelope.signature?.keyId);
  if (!key) errors.push('署名鍵がTrust Storeにありません');
  else if (!verifyDigest(envelope.release.digest, envelope.signature.value, key)) errors.push('Ed25519署名が不正です');
  return { ok: errors.length === 0, digest, errors };
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

export function validateRelease(payload, validators) {
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
  return { ok: errors.length === 0, errors };
}
