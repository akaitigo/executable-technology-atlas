#!/usr/bin/env node
import { execFileSync } from 'node:child_process';
import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { parse } from 'yaml';
import { canonicalJson, fixtureKeyPair, sha256, signDigest } from './lib/crypto.mjs';

const [catalogPath, ...subjectDirs] = process.argv.slice(2);
if (!catalogPath || subjectDirs.length === 0) {
  console.error('使い方: node scripts/generate-fixtures.mjs <catalog/stage1.yaml> <fixed-subject-checkout>...');
  process.exit(2);
}

const root = process.cwd();
const fixtureRoot = path.join(root, 'fixtures');
const releaseRoot = path.join(fixtureRoot, 'releases');
await mkdir(releaseRoot, { recursive: true });

async function readDocument(file) {
  return parse(await readFile(file, 'utf8'));
}

async function readEvidence(dir) {
  const evidenceDir = path.join(dir, 'evidence');
  let names = [];
  try { names = await readdir(evidenceDir); } catch { return []; }
  const records = [];
  for (const name of names.sort()) {
    if (!/\.evidence\.(json|ya?ml)$/.test(name)) continue;
    records.push(await readDocument(path.join(evidenceDir, name)));
  }
  return records;
}

function gitHead(dir) {
  try { return execFileSync('git', ['-C', dir, 'rev-parse', 'HEAD'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim(); }
  catch { return null; }
}

const catalog = await readDocument(catalogPath);
const coreDir = path.dirname(path.dirname(path.resolve(catalogPath)));
const { privateKey, publicKeyPem } = fixtureKeyPair();
const keyId = `fixture-ed25519-${sha256(publicKeyPem).slice(7, 23)}`;
const catalogPayload = { catalog, core: { commit: gitHead(coreDir), policyVersion: '1.0.0' } };
const catalogDigest = sha256(catalogPayload);
const catalogEnvelope = {
  schemaVersion: 1,
  kind: 'catalog-release',
  release: { version: `epoch-${catalog.coverage_epoch}`, uri: `urn:atlas:catalog:${catalog.coverage_epoch}:${gitHead(coreDir)}`, digest: catalogDigest, publishedAt: `${catalog.coverage_epoch}T00:00:00.000Z` },
  signature: { algorithm: 'Ed25519', keyId, value: signDigest(catalogDigest, privateKey) },
  payload: catalogPayload,
};

await mkdir(path.join(fixtureRoot, 'core'), { recursive: true });
await writeFile(path.join(fixtureRoot, 'trust.json'), `${JSON.stringify({ keys: [{ keyId, algorithm: 'Ed25519', publicKeyPem, usage: 'fixture-only' }] }, null, 2)}\n`);
await writeFile(path.join(fixtureRoot, 'core', 'catalog.release.json'), `${JSON.stringify(catalogEnvelope, null, 2)}\n`);

const registry = [];
for (const subjectDirInput of subjectDirs.sort()) {
  const subjectDir = path.resolve(subjectDirInput);
  const [atlas, mastery, coverage, sources, skillPackage, evidence] = await Promise.all([
    readDocument(path.join(subjectDir, 'atlas.yaml')),
    readDocument(path.join(subjectDir, 'mastery.yaml')),
    readDocument(path.join(subjectDir, 'coverage.yaml')),
    readDocument(path.join(subjectDir, 'sources.lock.yaml')),
    readDocument(path.join(subjectDir, 'skill.package.yaml')),
    readEvidence(subjectDir),
  ]);
  const payload = { atlas, mastery, coverage, sources, skillPackage, evidence, certificate: null };
  const commit = gitHead(subjectDir) ?? `fixture-snapshot-${sha256(payload).slice(7, 23)}`;
  const digest = sha256(payload);
  const envelope = {
    schemaVersion: 1,
    kind: 'atlas-release',
    release: { atlasId: atlas.id, version: skillPackage.atlas_release, commit, uri: `urn:atlas:release:${atlas.id}:${skillPackage.atlas_release}:${commit}`, digest, publishedAt: `${atlas.coverage.epoch}T00:00:00.000Z` },
    signature: { algorithm: 'Ed25519', keyId, value: signDigest(digest, privateKey) },
    payload,
  };
  const file = `${atlas.id}@${skillPackage.atlas_release.replaceAll('.', '_')}.release.json`;
  await writeFile(path.join(releaseRoot, file), `${JSON.stringify(envelope, null, 2)}\n`);
  registry.push({ atlasId: atlas.id, repository: atlas.repository.url.split('/').at(-1), version: skillPackage.atlas_release, commit, uri: envelope.release.uri, digest, signature: envelope.signature, file: `releases/${file}` });
}

await writeFile(path.join(fixtureRoot, 'registry.json'), `${JSON.stringify({ schemaVersion: 1, generatedBy: 'scripts/generate-fixtures.mjs', catalog: 'core/catalog.release.json', releases: registry }, null, 2)}\n`);
console.log(`Fixture生成済み: Catalog ${catalog.domains.flatMap((domain) => domain.subjects).length}件 / 固定Release ${registry.length}件`);
console.log(`Registry digest: ${sha256(canonicalJson(registry))}`);
