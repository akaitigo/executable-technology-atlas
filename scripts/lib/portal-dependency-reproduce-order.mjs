import Ajv2020 from 'ajv/dist/2020.js';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import addFormats from 'ajv-formats';
import { canonicalJson } from './crypto.mjs';

const CONTRACT_PATH='contracts/portal-dependency-reproduce-order.json';
const SCHEMA_PATH='contracts/schemas/portal-dependency-reproduce-order.schema.json';

export const EXPECTED_REPORT_RECORD_SCRIPTS=Object.freeze([
  'import:lifecycle:record',
  'distribution:record',
  'distribution:bindings:record',
  'distribution:gaps:record',
  'distribution:matrix:record',
  'definitive:root:gaps:record',
  'definitive:root:depth:record',
  'definitive:root:migration:record',
  'definitive:root:certificate:record',
  'definitive:root:declaration:record',
  'definitive:root:surface-readiness:record',
  'definitive:root:matrix-readiness:record',
  'definitive:root:record',
  'checkpoint:readiness:record'
]);

export const EXPECTED_VALIDATION_SCRIPTS=Object.freeze([
  'definitive:root:check',
  'import:lifecycle:check',
  'distribution:check',
  'distribution:bindings:check',
  'distribution:gaps:check',
  'distribution:matrix:check',
  'definitive:root:gaps:check',
  'definitive:root:depth:check',
  'definitive:root:migration:check',
  'definitive:root:certificate:check',
  'definitive:root:declaration:check',
  'definitive:root:surface-readiness:check',
  'definitive:root:matrix-readiness:check',
  'checkpoint:readiness:check',
  'dependency:negative',
  'dependency:refresh-readiness:check',
  'integration:status:check',
  'root:readiness:check'
]);

export const EXPECTED_IMPORT_AND_INDEX_SCRIPTS=Object.freeze(['import']);
export const EXPECTED_POST_IMPORT_SCRIPTS=Object.freeze(['non-regression','eval','sbom','build','perf','evidence','provenance']);

export async function loadPortalDependencyReproduceOrder(root=process.cwd()){
  const [orderBytes,schemaBytes,packageBytes]=await Promise.all([
    readFile(path.join(root,CONTRACT_PATH)),
    readFile(path.join(root,SCHEMA_PATH)),
    readFile(path.join(root,'package.json'))
  ]);
  return{
    order:JSON.parse(orderBytes),
    schema:JSON.parse(schemaBytes),
    packageDocument:JSON.parse(packageBytes),
    orderBytes,
    schemaBytes,
    packageBytes
  };
}

export function dependencyReproducePlan(order){
  return [
    ...order.reportRecordScripts,
    ...order.validationScripts,
    ...order.importAndIndexScripts,
    ...order.postImportScripts
  ];
}

export function validatePortalDependencyReproduceOrder(order,schema,packageDocument){
  const errors=[];const ajv=new Ajv2020({allErrors:true,strict:true});addFormats(ajv);const validate=ajv.compile(schema);if(!validate(order))errors.push(`Schema: ${ajv.errorsText(validate.errors)}`);
  if(canonicalJson(order.reportRecordScripts)!==canonicalJson(EXPECTED_REPORT_RECORD_SCRIPTS))errors.push('dependency-reproduce-report-order-weakened');
  if(canonicalJson(order.validationScripts)!==canonicalJson(EXPECTED_VALIDATION_SCRIPTS))errors.push('dependency-reproduce-validation-order-weakened');
  if(canonicalJson(order.importAndIndexScripts)!==canonicalJson(EXPECTED_IMPORT_AND_INDEX_SCRIPTS))errors.push('dependency-reproduce-import-order-weakened');
  if(canonicalJson(order.postImportScripts)!==canonicalJson(EXPECTED_POST_IMPORT_SCRIPTS))errors.push('dependency-reproduce-post-import-order-weakened');
  if(order.entrypoint!=='node scripts/refresh-portal-dependency-graph.mjs --record'||packageDocument.scripts?.['dependency:reproduce']!==order.entrypoint)errors.push('dependency-reproduce-entrypoint-rebound');
  const fullPlan=dependencyReproducePlan(order);
  const firstImportIndex=fullPlan.findIndex((item)=>order.importAndIndexScripts.includes(item));
  const lastValidationIndex=Math.max(...order.validationScripts.map((item)=>fullPlan.indexOf(item)));
  const lastImportIndex=Math.max(...order.importAndIndexScripts.map((item)=>fullPlan.indexOf(item)));
  const firstPostImportIndex=fullPlan.findIndex((item)=>order.postImportScripts.includes(item));
  if(!(firstImportIndex>lastValidationIndex&&firstPostImportIndex>lastImportIndex))errors.push('dependency-reproduce-stage-order-invalid');
  const graphCheck=order.graphCheck??{};
  if(graphCheck.auditBeforeWrite!==true||graphCheck.digestOnlyClosure!==false||graphCheck.graphFirstRefresh!==false||graphCheck.sameRunCurrentProofRequired!==true)errors.push('dependency-reproduce-graph-boundary-weakened');
  for(const script of fullPlan)if(typeof packageDocument.scripts?.[script]!=='string'||packageDocument.scripts[script].length===0)errors.push(`dependency-reproduce-script-missing:${script}`);
  return{ok:errors.length===0,errors:[...new Set(errors)],plan:fullPlan};
}

export function applyPortalDependencyReproduceOrderNegative(order,testCase){
  const mutated=structuredClone(order);
  if(testCase.mutation==='remove-report-stage')mutated.reportRecordScripts.pop();
  else if(testCase.mutation==='remove-validation-stage')mutated.validationScripts.pop();
  else if(testCase.mutation==='move-root-report-before-readiness'){
    mutated.reportRecordScripts=mutated.reportRecordScripts.filter((item)=>item!=='definitive:root:record');
    mutated.reportRecordScripts.unshift('definitive:root:record');
  }
  else if(testCase.mutation==='move-import-before-validation'){const moved=mutated.importAndIndexScripts.shift();mutated.reportRecordScripts=[moved,...mutated.reportRecordScripts];}
  else if(testCase.mutation==='allow-graph-first-refresh')mutated.graphCheck.graphFirstRefresh=true;
  else if(testCase.mutation==='allow-digest-only-closure')mutated.graphCheck.digestOnlyClosure=true;
  else throw new Error(`未知のdependency reproduce負例です: ${testCase.mutation}`);
  return mutated;
}
