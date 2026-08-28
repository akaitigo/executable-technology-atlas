#!/usr/bin/env node
import { readFile, readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { stringify } from 'yaml';
import { sha256 } from './lib/crypto.mjs';

const root=process.cwd();const records=new Map();const add=async(file,kind,license,source_ids,generated_by)=>{records.set(file,{path:file,digest:sha256(await readFile(path.join(root,file))),kind,license,source_ids,...(generated_by?{generated_by}:{})});};
const evidenceNames=(await readdir(path.join(root,'evidence'))).filter((name)=>/\.evidence\.json$/.test(name));for(const name of evidenceNames){const evidence=JSON.parse(await readFile(path.join(root,'evidence',name),'utf8'));await add(evidence.artifact.uri,evidence.kind==='benchmark'?'benchmark':evidence.kind==='skill-eval'?'skill-eval':'test-report','Apache-2.0',['reference-atlas-core-v1'],evidence.producer);}
await add('sbom.spdx.json','sbom','CC0-1.0',['npm-dependency-lock'],'scripts/generate-sbom.mjs');await add('sbom.npm.spdx.json','sbom','CC0-1.0',['npm-dependency-lock'],'scripts/generate-sbom.mjs');await add('public/og.png','generated','Apache-2.0',['fixture-catalog-release'],'OpenAI ImageGen');
await add('contracts/non-regression-baseline.json','source','Apache-2.0',['fixture-catalog-release']);await add('contracts/non-regression-mappings.json','source','Apache-2.0',['fixture-catalog-release']);
await add('evidence/non-regression-harness.json','document','Apache-2.0',['fixture-catalog-release'],'scripts/check-non-regression.mjs');
const document={schema_version:1,atlas_id:'executable-technology-atlas',generated_at:'2026-08-28T00:00:00Z',artifacts:[...records.values()].sort((a,b)=>a.path.localeCompare(b.path))};await writeFile(path.join(root,'provenance.yaml'),stringify(document,{lineWidth:0}));console.log(`Provenance生成済み: ${document.artifacts.length} artifacts`);
