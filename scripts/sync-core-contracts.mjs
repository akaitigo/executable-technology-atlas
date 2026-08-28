#!/usr/bin/env node
import { cp, mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { sha256 } from './lib/crypto.mjs';

const [coreDirInput] = process.argv.slice(2);
if (!coreDirInput) {
  console.error('使い方: node scripts/sync-core-contracts.mjs <fixed-reference-atlas-core-checkout>');
  process.exit(2);
}
const coreDir = path.resolve(coreDirInput);
const destination = path.join(process.cwd(), 'contracts', 'schemas');
await mkdir(destination, { recursive: true });
const names = ['atlas','mastery','coverage','sources-lock','skill-package','evidence','catalog','claim','completion-certificate','provenance','skill-eval','third-party'];
const files = [];
for (const name of names) {
  const source = path.join(coreDir, 'schemas', `${name}.schema.json`);
  const target = path.join(destination, `${name}.schema.json`);
  await cp(source, target);
  files.push({ path: `schemas/${name}.schema.json`, digest: sha256(await readFile(source)) });
}
const provenance = {
  schemaVersion: 1,
  source: 'https://github.com/akaitigo/reference-atlas-core',
  commit: execFileSync('git', ['-C', coreDir, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(),
  files,
};
await writeFile(path.join(process.cwd(), 'contracts', 'PROVENANCE.json'), `${JSON.stringify(provenance, null, 2)}\n`);
console.log(`Core契約を固定しました: ${provenance.commit} (${files.length} schemas)`);
