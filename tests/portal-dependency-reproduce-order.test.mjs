import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { applyPortalDependencyReproduceOrderNegative, loadPortalDependencyReproduceOrder, validatePortalDependencyReproduceOrder } from '../scripts/lib/portal-dependency-reproduce-order.mjs';

const root=process.cwd();
const source=await readFile(path.join(root,'scripts/refresh-portal-dependency-graph.mjs'),'utf8');
const negative=JSON.parse(await readFile(path.join(root,'fixtures/evidence-dependency/refresh-order-negative-cases.json'),'utf8'));

test('dependency reproduce order contractはreport→validation→import→post-import→graph auditを固定する',async()=>{
  const {order,schema,packageDocument}=await loadPortalDependencyReproduceOrder(root);
  const result=validatePortalDependencyReproduceOrder(order,schema,packageDocument);
  assert.equal(result.ok,true,result.errors.join('; '));
  assert.equal(result.plan.length,40);
  assert.deepEqual(result.plan.slice(0,3),['import:lifecycle:record','distribution:record','distribution:bindings:record']);
  assert.ok(result.plan.indexOf('definitive:root:record')>result.plan.indexOf('definitive:root:matrix-readiness:record'));
  assert.deepEqual(result.plan.slice(-4),['build','perf','evidence','provenance']);
});

test('dependency reproduce entrypointはshared planを参照し、graph write前auditを維持する',async()=>{
  for(const token of ["loadPortalDependencyReproduceOrder(root)","validatePortalDependencyReproduceOrder(order,orderSchema,packageDocument)","dependencyReproducePlan(order)","for(const script of plan)","auditPortalGraph(root,graph,schema)","if(!result.ok)throw new Error(result.errors.join('; '))"])assert.ok(source.includes(token),token);
});

test('dependency reproduce order negativeはorder driftとgraph-first closureを拒否する',async()=>{
  const {order,schema,packageDocument}=await loadPortalDependencyReproduceOrder(root);
  assert.equal(negative.cases.length,6);
  for(const item of negative.cases){
    const result=validatePortalDependencyReproduceOrder(applyPortalDependencyReproduceOrderNegative(order,item),schema,packageDocument);
    assert.equal(result.ok,false,item.caseId);
    assert.ok(result.errors.includes(item.expectedDiagnostic),`${item.caseId}: ${result.errors.join('; ')}`);
  }
});
