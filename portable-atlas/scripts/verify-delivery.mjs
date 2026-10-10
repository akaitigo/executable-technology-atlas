import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const manifest=JSON.parse(fs.readFileSync(path.join(root,'app/lib/migration-files.json'),'utf8'));
const expected=new Set(['app/lib/migration-files.json']);
for(const row of manifest.files){
 if(typeof row.path!=='string'||row.path.startsWith('/')||row.path.split('/').some(p=>p==='..'||!p||p.startsWith('.'))||expected.has(row.path))throw Error('Invalid or duplicate manifest path');
 expected.add(row.path);let file=root;
 for(const part of row.path.split('/')){file=path.join(file,part);if(fs.lstatSync(file).isSymbolicLink())throw Error('Symlink refused: '+row.path);}
 const bytes=fs.readFileSync(file);
 if(bytes.length!==row.bytes||createHash('sha256').update(bytes).digest('hex')!==row.sha256)throw Error('File mismatch: '+row.path);
}
let actual=0;
function walk(dir){for(const item of fs.readdirSync(dir,{withFileTypes:true})){const file=path.join(dir,item.name),relative=path.relative(root,file);if(item.isSymbolicLink())throw Error('Symlink refused: '+relative);if(item.isDirectory())walk(file);else{actual++;if(!expected.has(relative))throw Error('Unlisted file: '+relative);}}}
walk(root);if(actual!==expected.size)throw Error('File count mismatch');
console.log(JSON.stringify({status:'verified',files:actual,manifestFiles:manifest.files.length,scope:'distribution bytes only; not GUI or producer acceptance'}));
