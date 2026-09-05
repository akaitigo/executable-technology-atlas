import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { parse } from 'yaml';
import { canonicalJson, sha256 } from './crypto.mjs';

const SCOPE='portal-infrastructure-read-model';

export async function loadPortalRootSurfaceSources(root=process.cwd()){
  const masteryBytes=await readFile(path.join(root,'mastery.yaml'));
  const coverageBytes=await readFile(path.join(root,'coverage.yaml'));
  return{mastery:parse(masteryBytes.toString('utf8')),coverage:parse(coverageBytes.toString('utf8')),sourceDigests:{'mastery.yaml':sha256(masteryBytes),'coverage.yaml':sha256(coverageBytes)}};
}

export function buildPortalRootSurfaceInventory({mastery,coverage,sourceDigests},lock){
  const surfaces=(mastery.surfaces??[]).map((item)=>({id:item.id,title:item.title,applicability:item.applicability,rationale:item.rationale,targetSets:[...(item.target_sets??[])],requiredDeliverables:[...(item.required_deliverables??[])]}));
  const targets=(coverage.targets??[]).map((item)=>({id:item.id,title:item.title,targetSet:item.target_set,kind:item.kind,requirement:item.requirement,boundedCoverageState:item.state,claimIds:[...(item.claim_ids??[])],evidenceIds:[...(item.evidence_ids??[])],exclusion:item.exclusion??null}));
  return{
    schemaVersion:1,
    id:'portal-root-surface-inventory',
    atlasId:mastery.atlas_id,
    epoch:mastery.epoch,
    scope:SCOPE,
    classification:'bounded-root-artifact',
    sources:{...sourceDigests},
    denominator:{masterySurfaces:surfaces.length,coverageTargets:targets.length,sourcePolicy:'portal-v1-authored-contracts'},
    surfaces,
    targets,
    mapping:{status:'not-declared-in-v1-contract',inventedEdges:0,rationale:'Mastery SurfaceとCoverage Targetの個別edgeはv1正本に存在しないため、Portalは対応関係を推測または生成しない。'},
    boundary:{coreSubjectArtifactPath:lock.portalInfrastructureSurfaceInventory.coreSubjectArtifactPath,coreSubjectArtifactStatus:'missing',coreSubjectArtifactEffect:'none',subjectDefinitiveEffect:'none',distributionGapEffect:'none',completionEffect:'none',autoPromotion:false}
  };
}

export async function validatePortalRootSurfaceInventory(root,inventory,lock){
  const errors=[];const source=await loadPortalRootSurfaceSources(root);const expected=buildPortalRootSurfaceInventory(source,lock);const policy=lock.portalInfrastructureSurfaceInventory;
  const surfaceIds=(inventory.surfaces??[]).map((item)=>item.id);const targetIds=(inventory.targets??[]).map((item)=>item.id);
  if(inventory.schemaVersion!==1||inventory.id!=='portal-root-surface-inventory'||inventory.atlasId!==lock.atlasId||inventory.scope!==SCOPE||inventory.classification!=='bounded-root-artifact')errors.push('metadata-boundary-invalid');
  if(new Set(surfaceIds).size!==surfaceIds.length||canonicalJson(surfaceIds)!==canonicalJson(policy.expectedMasterySurfaceIds))errors.push('surface-denominator-reduced-or-reordered');
  if(new Set(targetIds).size!==targetIds.length||canonicalJson(targetIds)!==canonicalJson(policy.expectedCoverageTargetIds))errors.push('target-denominator-reduced-or-reordered');
  if(inventory.denominator?.masterySurfaces!==policy.expectedMasterySurfaceIds.length||inventory.denominator?.coverageTargets!==policy.expectedCoverageTargetIds.length)errors.push('denominator-count-mismatch');
  if(inventory.mapping?.status!=='not-declared-in-v1-contract'||inventory.mapping?.inventedEdges!==0)errors.push('mapping-fabricated');
  if(inventory.boundary?.coreSubjectArtifactPath!==policy.coreSubjectArtifactPath||inventory.boundary?.coreSubjectArtifactStatus!=='missing'||inventory.boundary?.coreSubjectArtifactEffect!=='none'||inventory.boundary?.subjectDefinitiveEffect!=='none'||inventory.boundary?.distributionGapEffect!=='none'||inventory.boundary?.completionEffect!=='none'||inventory.boundary?.autoPromotion!==false)errors.push('completion-boundary-weakened');
  if(canonicalJson(inventory)!==canonicalJson(expected))errors.push('source-denominator-drift');
  return{ok:errors.length===0,errors,summary:{masterySurfaces:surfaceIds.length,coverageTargets:targetIds.length,inventedEdges:inventory.mapping?.inventedEdges??null},digest:sha256(Buffer.from(`${JSON.stringify(inventory,null,2)}\n`))};
}

export function applyPortalRootSurfaceNegative(inventory,testCase){
  const mutated=structuredClone(inventory);
  if(testCase.mutation==='remove-surface')mutated.surfaces=mutated.surfaces.filter((item)=>item.id!==testCase.id);
  else if(testCase.mutation==='remove-target')mutated.targets=mutated.targets.filter((item)=>item.id!==testCase.id);
  else if(testCase.mutation==='invent-mapping')mutated.mapping={...mutated.mapping,status:'inferred',inventedEdges:1};
  else if(testCase.mutation==='promote-completion')mutated.boundary={...mutated.boundary,subjectDefinitiveEffect:'promote',completionEffect:'complete',autoPromotion:true};
  else throw new Error(`未知のPortal root surface負例です: ${testCase.mutation}`);
  return mutated;
}
