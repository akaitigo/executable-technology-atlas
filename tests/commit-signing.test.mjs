import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { sha256 } from '../scripts/lib/crypto.mjs';

const root=process.cwd();
const policy=JSON.parse(await readFile(path.join(root,'contracts/commit-signing-policy.json'),'utf8'));
const allowedSigners=path.join(root,policy.allowedSignersPath);
const commits=execFileSync('git',['rev-list',`${policy.enforcementFrom}^..HEAD`],{cwd:root,encoding:'utf8'}).trim().split('\n').filter(Boolean);

test('署名必須境界と公開allowed signersを固定する',async()=>{assert.equal(policy.requireCryptographicSignature,true);assert.equal(policy.requireDco,true);assert.equal(policy.historyRewrite,false);assert.equal(policy.forcePush,false);assert.equal(sha256(await readFile(allowedSigners)),policy.allowedSignersDigest);});
test('署名必須境界以降の全commitをgit verify-commitで検証する',()=>{assert.ok(commits.length>=1);for(const commit of commits){const verified=spawnSync('git',['-c','gpg.format=ssh','-c',`gpg.ssh.allowedSignersFile=${allowedSigners}`,'verify-commit',commit],{cwd:root,encoding:'utf8'});assert.equal(verified.status,0,`${commit}: ${verified.stdout}${verified.stderr}`);}});
