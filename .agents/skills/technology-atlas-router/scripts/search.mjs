#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import path from 'node:path';

const skillDir = path.dirname(path.dirname(new URL(import.meta.url).pathname));
const repositoryRoot = path.resolve(skillDir, '../../..');
const result = spawnSync(process.execPath, [path.join(repositoryRoot, 'scripts', 'atlas-portal.mjs'), 'search', ...process.argv.slice(2)], { cwd: repositoryRoot, stdio: 'inherit' });
process.exitCode = result.status ?? 1;
