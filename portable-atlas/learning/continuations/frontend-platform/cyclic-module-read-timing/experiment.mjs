import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
const root=new URL('./',import.meta.url),contracts=JSON.parse(readFileSync(new URL('contracts.json',root),'utf8'));
const rows=contracts.cases.map(c=>{
 const child=spawnSync(process.execPath,['driver.mjs',c.id],{cwd:root,encoding:'utf8',timeout:10000,env:{...process.env,NODE_OPTIONS:''}});
 const lines=child.stdout.trim().split('\n').filter(Boolean).map(line=>JSON.parse(line));
 const events=lines.filter(x=>Object.hasOwn(x,'event')),processInfo=lines.find(x=>x.process)?.process;
 const exception=child.stderr.trim()?JSON.parse(child.stderr):null;
 return {id:c.id,label:c.label,entry:c.entry,graph:c.graph,cycle:c.cycle,argv:['node','driver.mjs',c.id],pid:child.pid,process:processInfo,exit:child.status,signal:child.signal,spawn_error:child.error?.code??null,stdout:child.stdout,stderr:child.stderr,events,exception_class:exception?.class??null,exception_message:exception?.message??null,final_value:events.find(x=>x.event==='driver:done')?.value??null};
});
console.log(JSON.stringify({schema:1,engine:'Node native ES modules, separate process per fixture',rows}));
