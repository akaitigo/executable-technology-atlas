#!/usr/bin/env node
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { parse } from 'yaml';
import { fixtureKeyPair, sha256, signDigest } from './lib/crypto.mjs';

const root=process.cwd();const atlas=parse(await readFile(path.join(root,'atlas.yaml'),'utf8'));const skill=parse(await readFile(path.join(root,'skill.package.yaml'),'utf8'));const certificate=JSON.parse(await readFile(path.join(root,'evidence/completion-certificate.json'),'utf8'));const index=JSON.parse(await readFile(path.join(root,'app/data/index.generated.json'),'utf8'));
const manifestFiles=['atlas.yaml','mastery.yaml','coverage.yaml','sources.lock.yaml','skill.package.yaml','provenance.yaml'];const manifests=[];for(const file of manifestFiles)manifests.push({path:file,digest:sha256(await readFile(path.join(root,file)))});
const payload={atlas_id:atlas.id,version:skill.atlas_release,certificate_digest:sha256(certificate),index_digest:index.digest,manifests};const digest=sha256(payload);const {privateKey,publicKeyPem}=fixtureKeyPair();const keyId=`local-reproducible-${sha256(publicKeyPem).slice(7,23)}`;const envelope={schemaVersion:1,kind:'portal-release',release:{atlasId:atlas.id,version:skill.atlas_release,uri:`urn:atlas:release:${atlas.id}:${skill.atlas_release}:${digest.slice(7,23)}`,digest,publishedAt:'2026-08-28T00:00:00Z'},signature:{algorithm:'Ed25519',keyId,value:signDigest(digest,privateKey),identity:'local-evidence-only'},payload};
await mkdir(path.join(root,'release'),{recursive:true});await writeFile(path.join(root,'release/manifest.json'),`${JSON.stringify(envelope,null,2)}\n`);await writeFile(path.join(root,'release/public-key.pem'),publicKeyPem);console.log(`Portal Release生成済み: ${digest}`);
