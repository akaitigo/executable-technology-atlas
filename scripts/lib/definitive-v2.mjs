import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { sha256 } from './crypto.mjs';

const exactKeys=(value,expected)=>value&&JSON.stringify(Object.keys(value).sort())===JSON.stringify([...expected].sort());
const compile=(schema,errors,label)=>{const ajv=new Ajv2020({allErrors:true,strict:true});addFormats(ajv);try{const validator=ajv.compile(schema);return(value)=>{if(!validator(value))errors.push(`${label} Schema不適合: ${ajv.errorsText(validator.errors)}`);};}catch(error){errors.push(`${label} Schemaをcompileできません: ${error.message}`);return()=>{};}};

function validateCoreGate(gate,payload,lock){
  const errors=[];
  const fields=['schemaVersion','coreCommit','command','result','executedAt','runtimeIdentity','releaseDigest','definitiveDigest','certificateDigest','migrationDigest','inventoryClosure','runtimeProfiles','gapIds','diagnostics'];
  if(!exactKeys(gate,fields))errors.push('Definitive Core Gate resultのfield集合が不正です');
  if(gate?.schemaVersion!==1||gate?.coreCommit!==lock.coreCommit||gate?.command!==lock.gateCommand)errors.push('Definitive Core Gate resultが正式Core mainへ固定されていません');
  if(!['pass','fail'].includes(gate?.result)||!gate?.executedAt||Number.isNaN(Date.parse(gate.executedAt)))errors.push('Definitive Core Gate実行結果または時刻が不正です');
  if(!gate?.runtimeIdentity||typeof gate.runtimeIdentity!=='object'||Array.isArray(gate.runtimeIdentity)||!Object.keys(gate.runtimeIdentity).length)errors.push('Definitive Core Gate runtime identityが必要です');
  for(const [gateKey,payloadKey] of [['releaseDigest','releaseDigest'],['definitiveDigest','definitiveDigest'],['certificateDigest','certificateDigest'],['migrationDigest','migrationDigest']])if(gate?.[gateKey]!==payload?.[payloadKey])errors.push(`Definitive Core Gate ${gateKey} bindingが一致しません`);
  if(!Array.isArray(gate?.runtimeProfiles)||!Array.isArray(gate?.gapIds)||!Array.isArray(gate?.diagnostics))errors.push('Definitive Core GateのProfile/Gap/diagnostic配列が不正です');
  const inventory=gate?.inventoryClosure;if(!exactKeys(inventory,['status','required','classified','unclassified','openRequired','excluded','infeasible']))errors.push('Authority-derived inventory closure集計が不正です');
  if(gate?.result==='pass'&&(gate.gapIds?.length||gate.diagnostics?.length||inventory?.status!=='closed'||inventory?.unclassified!==0||inventory?.openRequired!==0||(gate.runtimeProfiles??[]).some((item)=>item.status!=='current'||!item.runtimeIdentity)))errors.push('Core Gate passに未Closure、Gap、または未検証Runtime Profileがあります');
  return errors;
}

export function validateDefinitiveV2Envelope(envelope,lock,schemas,verification){
  const errors=[...(verification?.errors??[])];const payload=envelope?.payload;
  if(envelope?.kind!=='portal-definitive-v2')errors.push('Definitive v2 kindが不正です');
  if(payload?.coreCommit!==lock.coreCommit)errors.push('Definitive v2が正式Core main commitへ固定されていません');
  const bindings=[['definitive','definitiveDigest'],['migration','migrationDigest'],['certificate','certificateDigest']];
  for(const [valueKey,digestKey] of bindings)if(!payload?.[valueKey]||payload?.[digestKey]!==sha256(payload[valueKey]))errors.push(`${valueKey} digest bindingが一致しません`);
  compile(schemas.definitive,errors,'Definitive manifest')(payload?.definitive);
  compile(schemas.migration,errors,'Definitive migration')(payload?.migration);
  compile(schemas.certificate,errors,'Definitive certificate')(payload?.certificate);
  const certificatePayload=payload?.certificate?Object.fromEntries(Object.entries(payload.certificate).filter(([key])=>key!=='signature')):null;
  if(!certificatePayload||payload?.certificate?.signature?.digest!==sha256(certificatePayload))errors.push('Definitive Certificate payload digestが一致しません');
  if(payload?.subjectId!==payload?.definitive?.atlas_id||payload?.atlasId!==payload?.definitive?.atlas_id||payload?.migration?.atlas_id!==payload?.atlasId||payload?.certificate?.atlas_id!==payload?.atlasId)errors.push('Definitive v2 Atlas/Subject bindingが一致しません');
  if(payload?.certificate?.commit!==payload?.sourceCommit)errors.push('Definitive Certificate commit bindingが一致しません');
  errors.push(...validateCoreGate(payload?.coreGate,payload,lock));
  if(payload?.coreGate?.result==='pass'&&verification?.trust?.usage!=='public-release')errors.push('subject-definitiveには公開Trust Keyが必要です');
  if(payload?.coreGate?.result==='pass'&&payload?.migration?.status!=='ready-for-audit')errors.push('Core Gate passにはready-for-audit Migrationが必要です');
  return{ok:errors.length===0,errors,payload,gate:payload?.coreGate??null};
}

export function projectDefinitiveV2(envelope,validated,verification){
  const payload=validated.payload;const gate=validated.gate;const complete=gate.result==='pass';
  return{schemaVersion:1,subjectId:payload.subjectId,atlasId:payload.atlasId,availability:'available',status:complete?'subject-definitive':'subject-definitive-incomplete',completionClass:complete?'subject-definitive':'not-definitive',coreContract:{status:'final',commit:payload.coreCommit},coreGate:gate,migration:{status:payload.migration.status,requiredActions:payload.migration.required_actions,historicalCertificate:payload.migration.historical_certificate},inventoryClosure:gate.inventoryClosure,runtimeProfiles:gate.runtimeProfiles,gapIds:gate.gapIds,artifacts:{definitive:{path:'definitive.yaml',digest:payload.definitiveDigest},migration:{path:'migrations/definitive-v2.yaml',digest:payload.migrationDigest},certificate:{path:'evidence/definitive-certificate.json',digest:payload.certificateDigest}},certificate:{schemaVersion:payload.certificate.schema_version,completionClass:payload.certificate.completion_class,issuedAt:payload.certificate.issued_at,commit:payload.certificate.commit,digest:payload.certificateDigest,trust:verification.trust},source:{repository:payload.repository,commit:payload.sourceCommit,releaseDigest:payload.releaseDigest,envelopeDigest:envelope.release.digest},readOnly:true,autoPromotion:false};
}

export function missingDefinitiveV2(subject,release){
  const states=release?.coverage?.states??{};
  return{schemaVersion:1,subjectId:subject.id,atlasId:release?.atlasId??null,availability:'missing',status:'subject-definitive-input-missing',completionClass:'not-definitive',coreContract:{status:'final',commit:'072d7ca77981f51754e824d70c6d4ecd55ea67e5'},coreGate:{result:'not-run',command:'atlas audit . --gate definitive',diagnostics:['署名済みDefinitive v2 bundleとCore Gate結果がありません']},migration:{status:'not-started',requiredActions:[],historicalCertificate:null},inventoryClosure:{status:'not-evaluated',required:null,classified:null,unclassified:null,openRequired:release?.coverage?.openRequired??null,excluded:states.excluded??0,infeasible:states.infeasible??0},runtimeProfiles:(release?.observedProfiles??[]).map((profile)=>({profile,status:'v1-evidence-observed-not-v2-verified',runtimeIdentity:null})),gapIds:['definitive.yaml','migrations/definitive-v2.yaml','evidence/definitive-certificate.json','core-gate:definitive'],artifacts:null,certificate:null,source:null,readOnly:true,autoPromotion:false,detailUrl:null};
}
