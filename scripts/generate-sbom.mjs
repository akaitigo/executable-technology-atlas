#!/usr/bin/env node
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { sha256 } from './lib/crypto.mjs';

const root=process.cwd();
const lock=JSON.parse(await readFile(path.join(root,'package-lock.json'),'utf8'));
const packages=[];
for(const [key,value] of Object.entries(lock.packages).filter(([key])=>key)){
  let installed={};try{installed=JSON.parse(await readFile(path.join(root,key,'package.json'),'utf8'));}catch{}
  const name=value.name??installed.name??key.split('node_modules/').at(-1);const license=value.license??installed.license??'NOASSERTION';const index=packages.length;
  packages.push({SPDXID:`SPDXRef-Package-${index+1}`,name,versionInfo:value.version??installed.version??'NOASSERTION',downloadLocation:value.resolved??'NOASSERTION',filesAnalyzed:false,licenseConcluded:license,licenseDeclared:license,externalRefs:value.integrity?[{referenceCategory:'PACKAGE-MANAGER',referenceType:'purl',referenceLocator:`pkg:npm/${encodeURIComponent(name)}@${value.version??'unknown'}`}]:undefined});
}
const dependencySbom={spdxVersion:'SPDX-2.3',dataLicense:'CC0-1.0',SPDXID:'SPDXRef-DOCUMENT',name:'executable-technology-atlas-npm-sbom',documentNamespace:`https://github.com/akaitigo/executable-technology-atlas/sbom/npm/${sha256(lock).slice(7)}`,creationInfo:{created:'2026-08-28T00:00:00Z',creators:['Tool: scripts/generate-sbom.mjs']},packages};
const releaseSbom={spdxVersion:'SPDX-2.3',dataLicense:'CC0-1.0',SPDXID:'SPDXRef-DOCUMENT',name:'executable-technology-atlas-release-sbom',documentNamespace:`https://github.com/akaitigo/executable-technology-atlas/sbom/release/${sha256(lock).slice(7)}`,creationInfo:{created:'2026-08-28T00:00:00Z',creators:['Tool: scripts/generate-sbom.mjs']},packages:[{SPDXID:'SPDXRef-Package-Portal',name:'executable-technology-atlas',versionInfo:'1.0.0',downloadLocation:'https://github.com/akaitigo/executable-technology-atlas',filesAnalyzed:false,licenseConcluded:'Apache-2.0',licenseDeclared:'Apache-2.0'}]};
await writeFile(path.join(root,'sbom.npm.spdx.json'),`${JSON.stringify(dependencySbom,null,2)}\n`);await writeFile(path.join(root,'sbom.spdx.json'),`${JSON.stringify(releaseSbom,null,2)}\n`);
console.log(`SBOM生成済み: release 1 / npm dependencies ${packages.length} packages`);
