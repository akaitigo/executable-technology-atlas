const test=require('node:test');
const assert=require('node:assert/strict');
const {contains}=require('./core.js');
test('弱いset：中ほどと遠い外側だけ',()=>{
  assert.equal(contains(3,2,5),true);
  assert.equal(contains(1,2,5),false);
  assert.equal(contains(6,2,5),false);
});
