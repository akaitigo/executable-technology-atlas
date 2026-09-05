#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { evaluatePortalEvidenceRefreshReadiness, loadPortalEvidenceRefreshPolicy } from './lib/portal-evidence-refresh-readiness.mjs';
import { evaluatePortalImportLifecycleVisibility } from './lib/portal-import-lifecycle-visibility.mjs';
import { evaluatePortalIntegrationStatus } from './lib/portal-integration-status.mjs';
import { evaluatePortalRootReadinessStatus } from './lib/portal-root-readiness-status.mjs';

const [command, ...args] = process.argv.slice(2);
const root = process.cwd();
const indexPath = path.join(root, 'app', 'data', 'index.generated.json');

function run(script, scriptArgs = []) {
  const result = spawnSync(process.execPath, [path.join(root, 'scripts', script), ...scriptArgs], { cwd: root, stdio: 'inherit' });
  process.exitCode = result.status ?? 1;
}

if (command === 'import') run('import-releases.mjs', args);
else if (command === 'verify') run('publication-gate.mjs', args);
else if (command === 'evidence-status') {
  const unknownArgs=args.filter((argument)=>argument!=='--require-ready');
  if(unknownArgs.length>0){console.error(`未対応の引数です: ${unknownArgs.join(' ')}`);process.exitCode=2;}
  else {
    const {policy,schema}=await loadPortalEvidenceRefreshPolicy(root);
    const result=await evaluatePortalEvidenceRefreshReadiness(root,policy,schema);
    console.log(JSON.stringify({ok:result.ok,errors:result.errors,...result.report},null,2));
    if(!result.ok||(args.includes('--require-ready')&&result.report.status!=='ready'))process.exitCode=1;
  }
}
else if(command==='integration-status'){
  if(args.length>0){console.error(`未対応の引数です: ${args.join(' ')}`);process.exitCode=2;}
  else{const result=await evaluatePortalIntegrationStatus(root);console.log(JSON.stringify({ok:result.ok,errors:result.errors,...result.report},null,2));if(!result.ok)process.exitCode=1;}
}
else if(command==='import-lifecycle'){
  if(args.length>0){console.error(`未対応の引数です: ${args.join(' ')}`);process.exitCode=2;}
  else{const result=await evaluatePortalImportLifecycleVisibility(root);console.log(JSON.stringify({ok:result.ok,errors:result.errors,...result.report},null,2));if(!result.ok)process.exitCode=1;}
}
else if(command==='root-readiness-status'){
  if(args.length>0){console.error(`未対応の引数です: ${args.join(' ')}`);process.exitCode=2;}
  else{const result=await evaluatePortalRootReadinessStatus(root);console.log(JSON.stringify({ok:result.ok,errors:result.errors,...result.report},null,2));if(!result.ok)process.exitCode=1;}
}
else if (command === 'search') {
  const index = JSON.parse(await readFile(indexPath, 'utf8'));
  const query = args.join(' ').toLocaleLowerCase('ja');
  const matches = index.subjects.filter((subject) => subject.searchText.includes(query));
  console.log(JSON.stringify(matches.map((subject) => ({ id: subject.id, title: subject.title, domain: subject.domain.title, catalogStatus: subject.status, release: subject.release ? { version: subject.release.version, status: subject.release.status, completion: subject.release.completion, verification: subject.release.verification, digest: subject.release.digest } : null })), null, 2));
} else {
  console.error('使い方: atlas-portal <import|verify|search|evidence-status|integration-status|import-lifecycle|root-readiness-status> [query|--require-ready]');
  process.exitCode = 2;
}
