import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import test from 'node:test';
import { parseDigestVerifiedJson } from '../app/lib/verified-json.mjs';

const digest = (bytes) => `sha256:${createHash('sha256').update(bytes).digest('hex')}`;
const response = (bytes, { ok=true, status=200 }={}) => ({ ok, status, arrayBuffer:async()=>bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength) });

test('固定bytesと一致するJSONだけを返す',async()=>{const bytes=Buffer.from('{"status":"pending-human"}\n');assert.deepEqual(await parseDigestVerifiedJson(response(bytes),digest(bytes)),{status:'pending-human'});});
test('取得後に改変されたJSONをdigest不一致で拒否する',async()=>{const locked=Buffer.from('{"decisions":0}\n');const changed=Buffer.from('{"decisions":1}\n');await assert.rejects(parseDigestVerifiedJson(response(changed),digest(locked)),/detail artifact digest mismatch/);});
test('不正な期待digestと不正JSONを拒否する',async()=>{const invalid=Buffer.from('not-json');await assert.rejects(parseDigestVerifiedJson(response(invalid),'sha256:invalid'),/expected digest is invalid/);await assert.rejects(parseDigestVerifiedJson(response(invalid),digest(invalid)),/detail JSON is invalid/);});
test('HTTP失敗を空のDecision一覧へ読み替えない',async()=>{const bytes=Buffer.from('{}');await assert.rejects(parseDigestVerifiedJson(response(bytes,{ok:false,status:503}),digest(bytes)),/detail HTTP 503/);});
