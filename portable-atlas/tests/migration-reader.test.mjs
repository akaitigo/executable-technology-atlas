import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { createHash } from 'node:crypto';
import { localReaderHandler } from '../app/lib/local-reader-http.mjs';
import { portalRoot,learningCatalog,learningRoutes,readAcceptedUnits,resolveLearningFile,migrationUnits } from '../app/lib/local-learning.mjs';
import manifest from '../app/lib/migration-files.json' with {type:'json'};

function request(url,headers={},method='GET'){
 const result={status:200,headers:{},body:null};
 const res={setHeader(k,v){result.headers[k.toLowerCase()]=v;},writeHead(status,headers={}){result.status=status;for(const [k,v] of Object.entries(headers))this.setHeader(k,v);},end(body){result.body=Buffer.isBuffer(body)?body.toString():body;}};
 localReaderHandler({url,headers:{host:'127.0.0.1:60000',...headers},method},res);
 return result;
}

test('既定142・候補追加6・未統合43を別一覧とし、191の一意な実体を保持',()=>{
 assert.equal(migrationUnits.length,191);assert.equal(new Set(migrationUnits.map(x=>x.id)).size,191);
 const catalog=learningCatalog();assert.equal(catalog.length,97);assert.equal(readAcceptedUnits(catalog).length,142);
 const groups=[['/',142,'正式142'],['/review/candidate148',6,'中央受入前'],['/review/pending',43,'未統合43']];
 for(const [url,n,label] of groups){const r=request(url);assert.equal(r.status,200,url);assert.ok(r.body.includes(label));assert.equal((r.body.match(/aria-describedby="topic-/g)??[]).length,n,url);}
 for(const row of migrationUnits){assert.equal(fs.realpathSync(path.join(portalRoot,row.location)),path.join(portalRoot,row.location));assert.ok(fs.statSync(path.join(portalRoot,row.location,'README.md')).isFile());}
});

test('191 READMEと収録HTMLをin-memory handlerで読む（browser/port/API/producer実行なし）',()=>{
 const routes=learningRoutes(learningCatalog());
 for(const row of migrationUnits){
  const r=request(`/lesson/${row.id}/README.md`,{accept:'text/html'});assert.equal(r.status,200,row.id);assert.ok(r.body.includes('教材文書reader'));
  const route=routes.find(x=>x.id===row.id);
  if(route.screen){const r=request(`/lesson/${row.id}/${route.screen}`,{accept:'text/html'});assert.equal(r.status,200,row.id+' screen');if(route.directPreview)assert.ok(r.body.includes('移行レビュー用コピー'),row.id+' migration notice');}
 }
});

test('Host・Origin・書込method・traversal・hidden・未登録教材を拒否',()=>{
 for(const [url,headers,method,expected] of [
 ['/',{host:'example.com:60000'},'GET',403],['/',{origin:'https://example.com'},'GET',403],['/',{},'POST',405],
 ['/lesson/unknown/README.md',{},'GET',404],['/lesson/kotlin~smart-cast-boundaries/%2e%2e%2fREADME.md',{},'GET',404],['/lesson/kotlin~smart-cast-boundaries/.env',{},'GET',404],
 ['/lesson/kotlin~smart-cast-boundaries/observations/resource-gate.json',{},'GET',404],['/omitted-reference',{},'GET',410]])assert.equal(request(url,headers,method).status,expected,url);
 const r=request('/');assert.equal(r.headers['x-content-type-options'],'nosniff');assert.ok(r.headers['content-security-policy'].includes("object-src 'none'"));
});

test('未選別ファイルと隣接7repoを偶然の存在で配信しない',()=>{
 const catalog=learningCatalog();assert.equal(catalog.filter(x=>x.original).length,7);
 for(const row of catalog.filter(x=>x.original)){assert.deepEqual(row.allowedFiles,[]);assert.equal(request(`/lesson/${row.id}/README.md`).status,404);}
 const row=migrationUnits[0],file=path.join(portalRoot,row.location,'private-unlisted.txt');assert.equal(fs.existsSync(file),false);
 try{fs.writeFileSync(file,'migration-owned negative fixture');assert.equal(request(`/lesson/${row.id}/private-unlisted.txt`).status,404);}finally{fs.unlinkSync(file);}
});

test('symlink先と不正受入manifestを拒否',()=>{
 const tmp=fs.mkdtempSync(path.join(fs.realpathSync(os.tmpdir()),'atlas-migration-boundary-'));
 try{
  fs.mkdirSync(path.join(tmp,'lesson'));fs.writeFileSync(path.join(tmp,'outside.txt'),'owned fixture');fs.symlinkSync('../outside.txt',path.join(tmp,'lesson/link.txt'));
  assert.throws(()=>resolveLearningFile([{id:'fixture',dir:path.join(tmp,'lesson'),allowedFiles:['link.txt']}],'fixture','link.txt'),/symlink/);
  fs.writeFileSync(path.join(tmp,'invalid.json'),JSON.stringify({schemaVersion:1,units:[{subject:'kotlin',unit:'smart-cast-boundaries',accepted:false,ui:'static'}]}));
  assert.throws(()=>readAcceptedUnits(learningCatalog(),path.join(tmp,'invalid.json')),/未受入/);
 }finally{fs.rmSync(tmp,{recursive:true,force:true});}
});

test('収録manifestの全ファイルが実バイトSHAに一致',()=>{
 for(const row of manifest.files){const file=path.join(portalRoot,row.path);assert.equal(fs.lstatSync(file).isSymbolicLink(),false,row.path);const b=fs.readFileSync(file);assert.equal(b.length,row.bytes,row.path);assert.equal(createHash('sha256').update(b).digest('hex'),row.sha256,row.path);}
});
