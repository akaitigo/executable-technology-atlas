import { lstat, mkdir, realpath, rename, writeFile } from 'node:fs/promises';
import path from 'node:path';

const COLLECTIONS = ['releases','depthReferences','authorityReviews','evidenceDependencies','fixedCommitAudits','definitiveV2'];
const SINGLETON_COLLECTIONS = COLLECTIONS.filter((name)=>name!=='releases');
const FILE_FIELDS = {
  releases:['file'],
  depthReferences:['file'],
  authorityReviews:['envelopeFile','archiveFile'],
  evidenceDependencies:['file'],
  fixedCommitAudits:['file'],
  definitiveV2:['file'],
};
const NEGATIVE_CASE_IDS=['duplicate-fixed-commit-subject','duplicate-release-identity','catalog-outside-subject','catalog-repository-rebind','duplicate-file-binding','fixture-root-path-escape','normalized-parent-segment','absolute-path','missing-file','directory-target','symlink-target','symlink-directory-target'];

function duplicateValues(items,keyFor){
  const seen=new Set();const duplicates=new Set();
  for(const item of items){const key=keyFor(item);if(!key)continue;if(seen.has(key))duplicates.add(key);else seen.add(key);}
  return [...duplicates].sort();
}

export async function validateRegistryPreflight(registry,fixtureRoot,catalog){
  const errors=[];
  const catalogSubjectValues=(catalog?.domains??[]).flatMap((domain)=>domain.subjects??[]);
  if(registry?.schemaVersion!==1)errors.push('Registry schemaVersionは1である必要があります');
  if(registry?.catalog!=='core/catalog.release.json')errors.push('Registry catalog pathが正本Pathと一致しません');
  for(const name of COLLECTIONS)if(!Array.isArray(registry?.[name]))errors.push(`Registry ${name}は配列である必要があります`);
  if(errors.length)return{result:'fail',errors,catalogSubjects:catalogSubjectValues.length,collections:{}};

  const catalogSubjects=new Map(catalogSubjectValues.map((subject)=>[subject.id,subject]));
  const catalogRepositories=new Set([...catalogSubjects.values()].map((subject)=>subject.repository));
  for(const name of SINGLETON_COLLECTIONS){
    for(const subjectId of duplicateValues(registry[name],(item)=>item?.subjectId))errors.push(`Registry ${name}に重複subjectIdがあります: ${subjectId}`);
    for(const item of registry[name]){
      const subject=catalogSubjects.get(item?.subjectId);
      if(!subject)errors.push(`Registry ${name}がCatalog外subjectを参照しています: ${item?.subjectId??'(missing)'}`);
      else if(subject.repository!==item?.repository)errors.push(`Registry ${name}のrepositoryがCatalogと一致しません: ${item.subjectId}`);
    }
  }
  for(const identity of duplicateValues(registry.releases,(item)=>item?.repository&&item?.version?`${item.repository}@${item.version}`:null))errors.push(`Registry releasesに重複Release identityがあります: ${identity}`);
  for(const digest of duplicateValues(registry.releases,(item)=>item?.digest))errors.push(`Registry releasesに重複digestがあります: ${digest}`);
  for(const item of registry.releases)if(!catalogRepositories.has(item?.repository))errors.push(`Registry releasesがCatalog外repositoryを参照しています: ${item?.repository??'(missing)'}`);

  const referencedFiles=[{collection:'catalog',index:0,field:'catalog',value:registry.catalog}];
  for(const name of COLLECTIONS)for(const[index,item]of registry[name].entries())for(const field of FILE_FIELDS[name])referencedFiles.push({collection:name,index,field,value:item?.[field]});
  const rootReal=await realpath(fixtureRoot);
  const registeredPaths=new Map();
  for(const reference of referencedFiles){
    const label=`${reference.collection}[${reference.index}].${reference.field}`;
    if(typeof reference.value!=='string'||!reference.value.length){errors.push(`Registry ${label}のPathがありません`);continue;}
    if(path.isAbsolute(reference.value)||path.win32.isAbsolute(reference.value)){errors.push(`Registry ${label}は絶対Pathを使用できません`);continue;}
    if(reference.value.split(/[\\/]/).includes('..')){errors.push(`Registry ${label}は親Directory参照を使用できません`);continue;}
    const resolved=path.resolve(rootReal,reference.value);
    const relative=path.relative(rootReal,resolved);
    if(!relative||relative.startsWith(`..${path.sep}`)||relative==='..'||path.isAbsolute(relative)){errors.push(`Registry ${label}がfixture root外を参照しています`);continue;}
    const prior=registeredPaths.get(relative);if(prior){errors.push(`Registry ${label}が同一Fileを重複bindingしています: ${prior}`);continue;}registeredPaths.set(relative,label);
    try{
      let current=rootReal;let stat=null;let symlinkFound=false;
      for(const segment of relative.split(path.sep)){current=path.join(current,segment);stat=await lstat(current);if(stat.isSymbolicLink()){symlinkFound=true;break;}}
      if(symlinkFound){errors.push(`Registry ${label}はsymlinkを経由できません`);continue;}
      if(!stat?.isFile()){errors.push(`Registry ${label}は通常Fileである必要があります`);continue;}
      const targetReal=await realpath(resolved);const targetRelative=path.relative(rootReal,targetReal);
      if(targetRelative.startsWith(`..${path.sep}`)||targetRelative==='..'||path.isAbsolute(targetRelative))errors.push(`Registry ${label}の実体がfixture root外です`);
    }catch{errors.push(`Registry ${label}のFileが存在しません`);}
  }
  return{result:errors.length?'fail':'pass',errors,catalogSubjects:catalogSubjects.size,collections:Object.fromEntries(COLLECTIONS.map((name)=>[name,registry[name].length])),referencedFiles:referencedFiles.length,duplicatePolicy:'reject',fileBindingPolicy:'one-registry-reference-per-file',pathPolicy:'fixture-root-regular-files-only',parentTraversalPolicy:'reject',symlinkPolicy:'reject-all-components'};
}

export async function recordRegistryPreflightFailure(reportPath,registryPreflight){
  await mkdir(path.dirname(reportPath),{recursive:true});const temporary=`${reportPath}.tmp`;await writeFile(temporary,`${JSON.stringify({schemaVersion:1,registry:registryPreflight,verdict:'fail'},null,2)}\n`);await rename(temporary,reportPath);
}

export function evaluateRegistryEvidence(registryPreflight,negativeFixture){
  const ids=new Set(negativeFixture?.cases?.map((item)=>item.id));
  const policyPass=registryPreflight?.result==='pass'&&registryPreflight?.catalogSubjects===97&&registryPreflight?.collections?.fixedCommitAudits===7&&registryPreflight?.duplicatePolicy==='reject'&&registryPreflight?.fileBindingPolicy==='one-registry-reference-per-file'&&registryPreflight?.pathPolicy==='fixture-root-regular-files-only'&&registryPreflight?.parentTraversalPolicy==='reject'&&registryPreflight?.symlinkPolicy==='reject-all-components';
  const negativePass=negativeFixture?.schemaVersion===1&&negativeFixture?.cases?.length===NEGATIVE_CASE_IDS.length&&NEGATIVE_CASE_IDS.every((id)=>ids.has(id))&&negativeFixture.cases.every((item)=>item.expectedResult==='last-known-good-preserved');
  return{ok:policyPass&&negativePass,policyPass,negativePass,catalogSubjects:registryPreflight?.catalogSubjects??0,fixedCommitAudits:registryPreflight?.collections?.fixedCommitAudits??0,negativeCases:negativeFixture?.cases?.length??0,expectedNegativeCases:NEGATIVE_CASE_IDS.length};
}
