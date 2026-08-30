#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import { readFile, stat, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { sha256 } from './lib/crypto.mjs';
import { validatePortalRootSurfaceInventory } from './lib/portal-root-surface-inventory.mjs';

const root=process.cwd();
const mode=process.argv[2]??'--check';
if(!['--check','--record'].includes(mode))throw new Error('使い方: node scripts/check-portal-root-definitive.mjs --check|--record');
const coreDir=path.resolve(process.env.ATLAS_CORE_DIR??path.join(root,'..','reference-atlas-core'));
const lock=JSON.parse(await readFile(path.join(root,'contracts/portal-root-definitive-lock.json'),'utf8'));
const reportPath=path.join(root,'evidence/portal-root-definitive-report.json');
const surfaceInventoryBytes=await readFile(path.join(root,lock.portalInfrastructureSurfaceInventory.path));
const surfaceInventory=JSON.parse(surfaceInventoryBytes);
const surfaceInventoryResult=await validatePortalRootSurfaceInventory(root,surfaceInventory,lock);
if(!surfaceInventoryResult.ok)throw new Error(`Portal root Surface Inventoryが正本分母と一致しません: ${surfaceInventoryResult.errors.join(', ')}`);
const coreHead=spawnSync('git',['rev-parse','HEAD'],{cwd:coreDir,encoding:'utf8'});
if(coreHead.status!==0||coreHead.stdout.trim()!==lock.coreCommit)throw new Error(`Core checkoutが固定commitではありません: ${coreHead.stdout.trim()}`);
const present=[];const missing=[];
for(const relative of lock.knownMissingArtifacts){try{if((await stat(path.join(root,relative))).isFile())present.push(relative);else missing.push(relative);}catch{missing.push(relative);}}
if(present.length)throw new Error(`Root Definitive lockのmissing artifactが存在します。実監査結果を更新してください: ${present.join(', ')}`);
const result=spawnSync('go',['run','./cmd/atlas','audit',root,'--gate','definitive'],{cwd:coreDir,encoding:'utf8'});
const combined=`${result.stdout??''}${result.stderr??''}`;
const observedBlockingArtifact=lock.knownMissingArtifacts.find((relative)=>combined.includes(`${relative}${lock.expectedDiagnosticSuffix}`));
if(result.status!==lock.expectedExitCode||!observedBlockingArtifact)throw new Error(`Portal root Definitive監査結果が既知必須artifactの失敗と一致しません: exit=${result.status} output=${combined}`);
const report={schemaVersion:1,atlasId:lock.atlasId,scope:'portal-root-only',core:{commit:lock.coreCommit,command:lock.command},result:'fail',exitCode:result.status,status:'root-definitive-incomplete',completionClass:lock.completionClass,knownMissingArtifacts:missing,failureOrdering:lock.failureOrdering,diagnosticClass:'known-required-root-artifact-unreadable',portalInfrastructureArtifacts:[{id:surfaceInventory.id,path:lock.portalInfrastructureSurfaceInventory.path,digest:sha256(surfaceInventoryBytes),status:'current',classification:surfaceInventory.classification,denominator:surfaceInventory.denominator,mappingStatus:surfaceInventory.mapping.status,inventedEdges:surfaceInventory.mapping.inventedEdges,coreSubjectArtifact:{path:surfaceInventory.boundary.coreSubjectArtifactPath,status:surfaceInventory.boundary.coreSubjectArtifactStatus,effect:surfaceInventory.boundary.coreSubjectArtifactEffect}}],boundary:{portalBoundedCertificate:'preserved-v1-local-evidence',subjectDefinitiveEffect:lock.subjectDefinitiveEffect,distributionStatus:'not-established',distributionGapEffect:lock.distributionGapEffect,completionEffect:lock.completionEffect,autoPromotion:false}};
const bytes=`${JSON.stringify(report,null,2)}\n`;
if(mode==='--record')await writeFile(reportPath,bytes);
else if(await readFile(reportPath,'utf8')!==bytes)throw new Error('Portal root Definitive reportが実監査結果と一致しません。--recordで再生成してください');
console.log(`Portal root Definitive: PASS / ${report.status} / missing=${missing.length} / completion_effect=none`);
