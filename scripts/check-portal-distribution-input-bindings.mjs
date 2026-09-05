#!/usr/bin/env node
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { buildPortalDistributionInputBindings, loadPortalDistributionBindingInputs, validatePortalDistributionInputBindings } from './lib/portal-distribution-input-bindings.mjs';

const root=process.cwd();const mode=process.argv[2]??'--check';if(!['--check','--record'].includes(mode))throw new Error('使い方: node scripts/check-portal-distribution-input-bindings.mjs --check|--record');
const output=path.join(root,'evidence/portal-distribution-input-bindings.json');const{indexBytes,index,schema}=await loadPortalDistributionBindingInputs(root);const document=buildPortalDistributionInputBindings(index,indexBytes);const result=await validatePortalDistributionInputBindings(root,document,schema);if(!result.ok)throw new Error(result.errors.join(', '));const bytes=`${JSON.stringify(document,null,2)}\n`;
if(mode==='--record')await writeFile(output,bytes);else if(await readFile(output,'utf8')!==bytes)throw new Error('Portal Distribution Input Bindingsが正本Indexと一致しません。--recordで再生成してください');
console.log(`Portal Distribution bindings: PASS / ${document.status} / release=${document.summary.releaseBindings}/${document.summary.subjects} / audits=${document.summary.fixedCommitAuditBindings} / definitive=${document.summary.definitiveV2Bindings}`);
