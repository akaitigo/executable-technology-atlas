import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { loadTrust, verifyEnvelope } from '../scripts/lib/validate.mjs';

const root = process.cwd();
const fixtureRoot = path.join(root,'fixtures');
const registry = JSON.parse(await readFile(path.join(fixtureRoot,'registry.json'),'utf8'));
const trusted = await loadTrust(fixtureRoot);
const envelope = JSON.parse(await readFile(path.join(fixtureRoot,registry.releases[0].file),'utf8'));

test('署名済みfixture Releaseを受理する', () => assert.equal(verifyEnvelope(envelope,trusted).ok,true));
test('署名後にPayloadが変わったReleaseを隔離する', () => { const tampered=structuredClone(envelope);tampered.payload.atlas.title+='改変';assert.equal(verifyEnvelope(tampered,trusted).ok,false); });
test('署名値が不正なReleaseを隔離する', () => { const tampered=structuredClone(envelope);tampered.signature.value=`A${tampered.signature.value.slice(1)}`;assert.equal(verifyEnvelope(tampered,trusted).ok,false); });
test('未知の鍵を拒否する', () => { const tampered=structuredClone(envelope);tampered.signature.keyId='unknown';assert.equal(verifyEnvelope(tampered,trusted).ok,false); });
test('97件を欠落なく索引する', async () => { const index=JSON.parse(await readFile(path.join(root,'app/data/index.generated.json'),'utf8'));assert.equal(index.subjects.length,97);assert.equal(index.verification.absent,90); });
