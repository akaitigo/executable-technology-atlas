#!/usr/bin/env node
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { buildPortalRootSurfaceInventory, loadPortalRootSurfaceSources, validatePortalRootSurfaceInventory } from './lib/portal-root-surface-inventory.mjs';

const root=process.cwd();const mode=process.argv[2]??'--check';
if(!['--check','--record'].includes(mode))throw new Error('使い方: node scripts/check-portal-root-surface-inventory.mjs --check|--record');
const lock=JSON.parse(await readFile(path.join(root,'contracts/portal-root-definitive-lock.json'),'utf8'));const relative=lock.portalInfrastructureSurfaceInventory.path;const target=path.join(root,relative);
if(mode==='--record'){const inventory=buildPortalRootSurfaceInventory(await loadPortalRootSurfaceSources(root),lock);await writeFile(target,`${JSON.stringify(inventory,null,2)}\n`);}
const inventory=JSON.parse(await readFile(target,'utf8'));const result=await validatePortalRootSurfaceInventory(root,inventory,lock);
if(!result.ok)throw new Error(`Portal root Surface Inventory不一致: ${result.errors.join(', ')}`);
console.log(`Portal root Surface Inventory: PASS / ${result.summary.masterySurfaces} surfaces / ${result.summary.coverageTargets} targets / invented edges=${result.summary.inventedEdges}`);
