import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const script=path.join(root,'scripts/rebuild-seed-databases.py');
const run=(...args)=>spawnSync('python3',[script,...args],{encoding:'utf8',timeout:15000});
function temporary(fn){const dir=fs.mkdtempSync(path.join(os.tmpdir(),'atlas-seed-test-'));try{fn(dir);}finally{fs.rmSync(dir,{recursive:true,force:true});}}

test('8個の合成DBを別SQLite接続から読み、固定の整数表を確認する',()=>temporary(dir=>{
 const out=path.join(dir,'generated');const result=run('--output-dir',out);assert.equal(result.status,0,result.stderr);
 const report=JSON.parse(fs.readFileSync(path.join(out,'seed-result.json'),'utf8'));
 assert.equal(report.kind,'seed-regeneration-not-historical-evidence');assert.equal(report.outputs.length,8);assert.equal(report.nativeWALExperimentRun,false);
 const read=spawnSync('python3',['-c',`import json,sqlite3,sys,pathlib
out={}
for p in sorted(pathlib.Path(sys.argv[1]).glob('*.sqlite')):
 c=sqlite3.connect('file:'+str(p)+'?mode=ro',uri=True)
 out[p.stem]=dict(rows=c.execute('select id,value from evidence order by id').fetchall(),columns=[x[1] for x in c.execute('pragma table_info(evidence)')],integrity=c.execute('pragma quick_check').fetchone()[0]);c.close()
print(json.dumps(out))`,out],{encoding:'utf8',timeout:15000});
 assert.equal(read.status,0,read.stderr);const data=JSON.parse(read.stdout);
 const expected={stale:21,fresh:21,rollback:11,busy:11,'stale-small':10,'fresh-high':102,'busy-zero':2,'rollback-high':110};
 assert.deepEqual(Object.keys(data).sort(),Object.keys(expected).sort());
 for(const [key,value] of Object.entries(expected)){assert.deepEqual(data[key].rows,[[1,value]]);assert.deepEqual(data[key].columns,['id','value']);assert.equal(data[key].integrity,'ok');}
}));
test('既存の出力先を拒否し、元の内容を保持する',()=>temporary(dir=>{
 const out=path.join(dir,'exists');fs.mkdirSync(out);fs.writeFileSync(path.join(out,'keep.txt'),'owned marker');
 const result=run('--output-dir',out);assert.equal(result.status,2);assert.deepEqual(fs.readdirSync(out),['keep.txt']);assert.equal(fs.readFileSync(path.join(out,'keep.txt'),'utf8'),'owned marker');
}));
test('path traversal・重複・非整数のseedを出力前に拒否する',()=>temporary(dir=>{
 for(const [name,cases] of [['path',[{id:'../outside',value:1}]],['duplicate',[{id:'same',value:1},{id:'same',value:2}]],['type',[{id:'value',value:'1'}]]]){
  const seed=path.join(dir,name+'.json');fs.writeFileSync(seed,JSON.stringify({schemaVersion:1,kind:'synthetic-sqlite-learning-seed',cases}));const out=path.join(dir,name);
  const result=run('--seed',seed,'--output-dir',out);assert.equal(result.status,2,result.stderr);assert.equal(fs.existsSync(out),false);
 }
}));
test('配送tree内を出力先に指定しても原票を変更しない',()=>{
 const out=path.join(root,'seeds');const before=fs.readFileSync(path.join(out,'wal-snapshot-values.json'));
 const result=run('--output-dir',out);assert.equal(result.status,2);assert.match(result.stderr,/outside the delivery tree/);assert.deepEqual(fs.readFileSync(path.join(out,'wal-snapshot-values.json')),before);
});
