import assert from 'node:assert/strict';
import test from 'node:test';
import { FIXED_CORE_CHECKOUT_PATH, buildCoreCheckoutCandidates, resolveCoreCheckout } from '../scripts/lib/core-checkout.mjs';

const root='/workspace/executable-technology-atlas';
const expected='072d7ca77981f51754e824d70c6d4ecd55ea67e5';

test('core checkout candidatesはenv > fixed tmp > adjacentの順で重複なく構成する',()=>{
  const candidates=buildCoreCheckoutCandidates(root,{env:{ATLAS_CORE_DIR:'/tmp/custom-core'}});
  assert.deepEqual(candidates,[
    {path:'/tmp/custom-core',source:'env',strict:true},
    {path:FIXED_CORE_CHECKOUT_PATH,source:'fixed-tmp',strict:false},
    {path:'/workspace/reference-atlas-core',source:'adjacent',strict:false}
  ]);
});

test('core checkout resolverはenv未指定時にfixed tmpの一致commitを優先する',()=>{
  const result=resolveCoreCheckout(root,expected,{env:{},probe:(candidate)=>candidate===FIXED_CORE_CHECKOUT_PATH?{status:0,commit:expected,stderr:''}:{status:0,commit:'46db1eb0e68d00c09f34994dd66ad6d44d3f6ef1',stderr:''}});
  assert.deepEqual(result,{coreDir:FIXED_CORE_CHECKOUT_PATH,source:'fixed-tmp',expectedCommit:expected});
});

test('core checkout resolverは明示ATLAS_CORE_DIR不一致を即拒否する',()=>{
  assert.throws(()=>resolveCoreCheckout(root,expected,{env:{ATLAS_CORE_DIR:'/tmp/wrong-core'},probe:()=>({status:0,commit:'deadbeef',stderr:''})}),/ATLAS_CORE_DIR does not match required commit/);
});

test('core checkout resolverは一致候補がなければfail-closedする',()=>{
  assert.throws(()=>resolveCoreCheckout(root,expected,{env:{},probe:(candidate)=>({status:0,commit:candidate.includes('reference-atlas-core')?'46db1eb0e68d00c09f34994dd66ad6d44d3f6ef1':'bad',stderr:''})}),/Core checkoutが正式main固定commitではありません/);
});
