import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { loadTrust, schemaValidators, validateCompletionCertificate, validateRelease, verifyEnvelope } from '../scripts/lib/validate.mjs';

const root = process.cwd();
const fixtureRoot = path.join(root,'fixtures');
const registry = JSON.parse(await readFile(path.join(fixtureRoot,'registry.json'),'utf8'));
const trusted = await loadTrust(fixtureRoot);
const envelope = JSON.parse(await readFile(path.join(fixtureRoot,registry.releases[0].file),'utf8'));

test('署名済みfixture Releaseを受理する', () => assert.equal(verifyEnvelope(envelope,trusted).ok,true));
test('署名後にPayloadが変わったReleaseを隔離する', () => { const tampered=structuredClone(envelope);tampered.payload.atlas.title+='改変';assert.equal(verifyEnvelope(tampered,trusted).ok,false); });
test('署名値が不正なReleaseを隔離する', () => { const tampered=structuredClone(envelope);tampered.signature.value=`A${tampered.signature.value.slice(1)}`;assert.equal(verifyEnvelope(tampered,trusted).ok,false); });
test('未知の鍵を拒否する', () => { const tampered=structuredClone(envelope);tampered.signature.keyId='unknown';assert.equal(verifyEnvelope(tampered,trusted).ok,false); });
test('Trust Storeのfixture-only分類を失わない', () => assert.equal(verifyEnvelope(envelope,trusted).trust.usage,'fixture-only'));
test('completeをCertificateなしで宣言したReleaseを拒否する', async () => { const validators=await schemaValidators(path.join(root,'contracts/schemas'));const payload=structuredClone(envelope.payload);payload.atlas.status='complete';const result=validateRelease(payload,validators,envelope.release);assert.equal(result.ok,false);assert.ok(result.errors.some((error)=>error.includes('Completion Certificate'))); });
test('CertificateのPayload digest改変を拒否する', async () => { const validators=await schemaValidators(path.join(root,'contracts/schemas'));const payload=structuredClone(envelope.payload);payload.certificate=JSON.parse(await readFile(path.join(root,'evidence/completion-certificate.json'),'utf8'));payload.certificate.atlas_id=payload.atlas.id;payload.certificate.atlas_release=payload.skillPackage.atlas_release;payload.certificate.coverage_epoch=payload.atlas.coverage.epoch;payload.certificate.authority_lock_digest=payload.coverage.authority_lock_digest;payload.certificate.core_policy_version=payload.atlas.completion.policy_version;const result=validateCompletionCertificate(payload,validators,envelope.release);assert.equal(result.ok,false);assert.ok(result.errors.some((error)=>error.includes('payload digest'))); });
test('97件を欠落なく索引する', async () => { const index=JSON.parse(await readFile(path.join(root,'app/data/index.generated.json'),'utf8'));assert.equal(index.subjects.length,97);assert.equal(index.verification.absent,90); });
test('IndexとImport Reportを一時Fileからatomic replaceする', async () => { const importer=await readFile(path.join(root,'scripts/import-releases.mjs'),'utf8');assert.match(importer,/rename\(outputTemporary, output\)/);assert.match(importer,/rename\(reportTemporary, reportPath\)/); });
