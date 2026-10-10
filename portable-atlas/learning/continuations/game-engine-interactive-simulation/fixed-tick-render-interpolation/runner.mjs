import {simulate} from './producer.mjs';import {readFile} from 'node:fs/promises';
const cases=JSON.parse(await readFile(new URL('cases.json',import.meta.url)));const [id='normal-5',override]=process.argv.slice(2);const started=new Date().toISOString();let result;
try{const c=cases.find(x=>x.id===id);if(!c)throw Error('UNKNOWN_CASE');result=simulate(override===undefined?c.input:JSON.parse(override));}catch(e){result={status:'REFUSED',reason:e.message,trace:[],ticks:[]};}
console.log(JSON.stringify({started,completed:new Date().toISOString(),id,result,node:process.version}));process.exitCode=result.status==='OK'?0:2;
