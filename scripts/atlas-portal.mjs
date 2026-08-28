#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import path from 'node:path';

const [command, ...args] = process.argv.slice(2);
const root = process.cwd();
const indexPath = path.join(root, 'app', 'data', 'index.generated.json');

function run(script, scriptArgs = []) {
  const result = spawnSync(process.execPath, [path.join(root, 'scripts', script), ...scriptArgs], { cwd: root, stdio: 'inherit' });
  process.exitCode = result.status ?? 1;
}

if (command === 'import') run('import-releases.mjs', args);
else if (command === 'verify') run('publication-gate.mjs', args);
else if (command === 'search') {
  const index = JSON.parse(await readFile(indexPath, 'utf8'));
  const query = args.join(' ').toLocaleLowerCase('ja');
  const matches = index.subjects.filter((subject) => subject.searchText.includes(query));
  console.log(JSON.stringify(matches.map((subject) => ({ id: subject.id, title: subject.title, domain: subject.domain.title, catalogStatus: subject.status, release: subject.release ? { version: subject.release.version, status: subject.release.status, completion: subject.release.completion, verification: subject.release.verification, digest: subject.release.digest } : null })), null, 2));
} else {
  console.error('使い方: atlas-portal <import|verify|search> [query]');
  process.exitCode = 2;
}
