import {readFileSync,writeFileSync,mkdirSync,readdirSync,statSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {join,relative,dirname} from 'node:path';
const root=fileURLToPath(new URL('./',import.meta.url)),digest=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const tree=dir=>readdirSync(dir).flatMap(n=>statSync(join(dir,n)).isDirectory()?tree(join(dir,n)):[join(dir,n)]);
const args=process.argv.slice(2);
if(!args.length){const p=spawnSync(process.execPath,['checker.mjs'],{cwd:root,stdio:'inherit',env:{...process.env,NODE_OPTIONS:''}});process.exitCode=p.status??1;}
else if(args.length!==1||args[0]!=='--record'){console.error('use node runner.mjs [--record]');process.exitCode=2;}
else{
 const id=new Date().toISOString().replace(/[-:.]/g,'')+'-cycle',dir=join(root,'observations',id);mkdirSync(join(root,'observations'),{recursive:true});mkdirSync(dir);
 // Refuse an existing named receipt, and never replace an old raw.
 const p=spawnSync(process.execPath,['experiment.mjs'],{cwd:root,encoding:'utf8',env:{...process.env,NODE_OPTIONS:''}});
 writeFileSync(join(dir,'command.json'),JSON.stringify({argv:['node','experiment.mjs'],exit:p.status,stdout:p.stdout,stderr:p.stderr},null,2)+'\n',{flag:'wx'});
 if(p.status!==0){process.exitCode=p.status??1;}
 else{
  const names=['contracts.json','expected-table.json','README.md','sources.json','coverage.json','route.mjs','driver.mjs','experiment.mjs','checker.mjs','runner.mjs','index.html','app.js','styles.css','skills/atlas-cyclic-module-read-timing/SKILL.md',...tree(join(root,'fixtures')).map(f=>relative(root,f))];
  const raw=JSON.parse(p.stdout);raw.run_id=id;raw.environment={node:process.version,platform:process.platform,arch:process.arch,dependencies:'Node built-ins',node_options_for_child:'empty'};raw.source_digests=Object.fromEntries(names.map(n=>[n,digest(join(root,n))]));
  for(const n of ['contracts.json','expected-table.json',...names.filter(n=>n.startsWith('fixtures/')),'driver.mjs']){const out=join(dir,'source',n);mkdirSync(dirname(out),{recursive:true});writeFileSync(out,readFileSync(join(root,n)),{flag:'wx'});}
  writeFileSync(join(dir,'raw.json'),JSON.stringify(raw,null,2)+'\n',{flag:'wx'});
  writeFileSync(join(dir,'artifact-index.json'),JSON.stringify({excludes_self:true,files:Object.fromEntries(tree(dir).map(f=>[relative(dir,f),digest(f)]))},null,2)+'\n',{flag:'wx'});
  writeFileSync(join(root,'observation-data.js'),'window.CYCLE_OBSERVATION='+JSON.stringify(raw)+';\n');console.log(JSON.stringify({run_id:id,cases:5,distinct_child_pids:new Set(raw.rows.map(r=>r.pid)).size,exit:0}));
 }
}
