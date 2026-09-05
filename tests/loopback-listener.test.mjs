import test from 'node:test';
import assert from 'node:assert/strict';
import { parseLsofRecords,verifyLoopbackRecords } from '../scripts/verify-loopback-listener.mjs';

test('127.0.0.1:4173の所有PIDだけを受理する',()=>{
  const records=parseLsofRecords('p4123\ncnode\nn127.0.0.1:4173\n');
  assert.deepEqual(records,[{pid:'4123',command:'node',address:'127.0.0.1:4173'}]);
  assert.deepEqual(verifyLoopbackRecords(records),{ok:true,expected:'127.0.0.1:4173',listeners:records,errors:[]});
});

test('listenerなし、wildcard、IPv6 wildcard、別portをfail closedで拒否する',()=>{
  assert.equal(verifyLoopbackRecords([]).ok,false);
  for (const address of ['*:4173','0.0.0.0:4173','[::]:4173','127.0.0.1:3000']) {
    const result=verifyLoopbackRecords([{pid:'42',command:'node',address}]);
    assert.equal(result.ok,false,address);
    assert.match(result.errors.join('\n'),/許可されないbind address/);
  }
});

test('正しいlistenerと不正listenerの混在を成功扱いしない',()=>{
  const result=verifyLoopbackRecords([
    {pid:'42',command:'node',address:'127.0.0.1:4173'},
    {pid:'43',command:'node',address:'*:4173'}
  ]);
  assert.equal(result.ok,false);
});
