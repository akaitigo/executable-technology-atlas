#!/usr/bin/env node
import { readFile, readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { sha256 } from './lib/crypto.mjs';
import { parse } from 'yaml';

const root=process.cwd();const names=(await readdir(path.join(root,'evidence'))).filter((name)=>/\.evidence\.json$/.test(name));
const coverage=parse(await readFile(path.join(root,'coverage.yaml'),'utf8'));
const harnesses={'portal.import.integrity':'scripts/import-releases.mjs','portal.ui.build':'app/page.tsx','portal.router.eval':'scripts/run-evals.mjs','portal.performance.budget':'scripts/performance-budget.mjs','portal.security.headers':'public/_headers','portal.publication.sbom':'scripts/generate-sbom.mjs'};
for(const name of names){const file=path.join(root,'evidence',name);const record=JSON.parse(await readFile(file,'utf8'));const bytes=await readFile(path.join(root,record.artifact.uri));record.artifact.digest=sha256(bytes);record.artifact.size_bytes=bytes.length;record.source_digest=coverage.authority_lock_digest;record.harness_path=harnesses[record.id];record.harness_digest=sha256(await readFile(path.join(root,record.harness_path)));await writeFile(file,`${JSON.stringify(record,null,2)}\n`);}
console.log(`Evidence artifact digest更新済み: ${names.length} records`);
