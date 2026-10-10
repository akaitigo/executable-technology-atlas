import assert from 'node:assert/strict';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {SOURCES} from './sources.mjs';
import * as a from './importer-a.mjs';
import * as b from './importer-b.mjs';
import {journal} from './journal.mjs';
const startedAt=new Date().toISOString(),root=new URL('./',import.meta.url),hash=b=>createHash('sha256').update(b).digest('hex');
const sourceHashes=Object.fromEntries(await Promise.all(SOURCES.map(async f=>[f,hash(await readFile(new URL(f,root)))])));
const observations=[];
let checks=0;
function sample(id,value,expected){const state={views:{a:a.read(),b:b.read()},namespaceSame:a.namespace()===b.namespace(),journal:journal()};assert.deepEqual(state.views,{a:{live:expected,snapshot:0},b:{live:expected,snapshot:0}},id);assert.equal(state.namespaceSame,true);assert.equal(state.journal.evaluationCounts.counter,1);checks+=3;observations.push({id,at:new Date().toISOString(),value,state});}
sample('initial',null,0);sample('a-increment',a.mutate(),1);sample('b-increment',b.mutate(),2);sample('zero',a.mutate(0),2);
const imported=a.assignImportedBinding();assert.equal(imported.name,'TypeError');assert.equal(imported.rejected,true);checks+=2;sample('assign-import',imported,2);
const namespace=b.assignNamespace();assert.equal(namespace.name,'TypeError');assert.equal(namespace.rejected,true);checks+=2;sample('assign-namespace',namespace,2);
const again=await import('./counter.mjs');assert.equal(again,a.namespace());checks++;sample('reimport',{sameNamespace:true,ordinal:again.evaluationOrdinal},2);
assert.throws(()=>a.mutate(NaN),RangeError);checks++;sample('invalid',{rejected:true,name:'RangeError'},2);sample('minus',a.mutate(-1),1);
const failures=[];
for(const [id,url,name,code] of [['loading','./missing-module.mjs','Error','ERR_MODULE_NOT_FOUND'],['syntax','./bad-syntax.mjs','SyntaxError',null]]){try{await import(url);throw Error('expected rejection');}catch(error){assert.equal(error.name,name);if(code)assert.equal(error.code,code);const result={id,input:url,name:error.name,code:error.code||null};failures.push(result);checks++;}}
const report={kind:'actual-node-file-module-loader-not-browser-evidence',startedAt,completedAt:new Date().toISOString(),environment:{node:process.version,platform:process.platform,arch:process.arch},sourceHashes,checks,passed:true,observations,failures,limitations:['Node file loader only; HTTP/MIME/browser failure names are separate','same URL within one Node process; no cycles or other realms tested']};
const args=process.argv.slice(2);
if(args.length){assert.equal(args[0],'--record');assert.equal(args.length,2);assert.match(args[1],/^[a-z][a-z0-9-]+$/);await mkdir(new URL('observations/',root),{recursive:true});const dir=new URL('observations/'+args[1]+'/',root);await mkdir(dir);await writeFile(new URL('node.json',dir),JSON.stringify(report,null,2)+'\n',{flag:'wx'});}
console.log(JSON.stringify(report,null,2));
