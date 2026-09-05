#!/usr/bin/env node
import { execFileSync } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fixtureKeyPair, sha256, signDigest } from './lib/crypto.mjs';

const root = process.cwd();
const sourceRepository = path.resolve(process.argv[2] ?? path.join(root, '..', 'frontend-behavior-atlas'));
const lock = JSON.parse(await readFile(path.join(root, 'contracts', 'depth-reference-lock.json'), 'utf8'));
const sourceBytes = execFileSync('git', ['show', `${lock.sourceCommit}:${lock.sourcePath}`], { cwd:sourceRepository, encoding:'utf8', maxBuffer:10_000_000 });
if (sha256(sourceBytes) !== lock.sourceDigest) throw new Error(`Source digest mismatch: ${sha256(sourceBytes)}`);
const payload = JSON.parse(sourceBytes);
const digest = sha256(payload);
const { privateKey, publicKeyPem } = fixtureKeyPair();
const keyId = `fixture-ed25519-${sha256(publicKeyPem).slice(7,23)}`;
const release = {
  subjectId:lock.subjectId, atlasId:lock.atlasId, repository:lock.repository,
  version:lock.referenceId, commit:lock.sourceCommit, path:lock.sourcePath,
  uri:`urn:atlas:depth-reference:${lock.atlasId}:${lock.sourceCommit}`,
  digest, publishedAt:'2026-08-28T00:00:00Z',
};
const envelope = {
  schemaVersion:1, kind:'portal-depth-reference', release,
  signature:{ algorithm:'Ed25519', keyId, value:signDigest(digest,privateKey) },
  source:{ digest:lock.sourceDigest, bytes:sourceBytes }, payload,
};
const fixtureFile = `depth-references/${lock.subjectId}@${lock.sourceCommit}.json`;
await mkdir(path.join(root,'fixtures','depth-references'),{recursive:true});
await writeFile(path.join(root,'fixtures',fixtureFile),`${JSON.stringify(envelope,null,2)}\n`);
const registryPath=path.join(root,'fixtures','registry.json');
const registry=JSON.parse(await readFile(registryPath,'utf8'));
registry.depthReferences=[{subjectId:lock.subjectId,atlasId:lock.atlasId,repository:lock.repository,commit:lock.sourceCommit,digest,sourceDigest:lock.sourceDigest,file:fixtureFile}];
await writeFile(registryPath,`${JSON.stringify(registry,null,2)}\n`);
console.log(`Depth Reference fixture生成済み: ${lock.subjectId} / ${payload.axes.length} axes / ${digest}`);
