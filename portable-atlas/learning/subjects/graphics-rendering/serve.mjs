import http from 'node:http';
import {readFile} from 'node:fs/promises';
const root=new URL('./',import.meta.url);
const cases=JSON.parse(await readFile(new URL('scenes.json',root),'utf8')).cases;
const allowed=new Map([['/','index.html'],...['index.html','lesson.js','README.md','scope.json','raster.py','verify.py','observations/cpu-attempt-01/run.json'].map(f=>['/'+f,f])]);
for(const c of cases)for(const m of ['depth','painter']){const f=`observations/cpu-attempt-01/${c.id}-${m}.png`;allowed.set('/'+f,f);}
const server=http.createServer(async(req,res)=>{const f=allowed.get(req.url);if(req.method!=='GET'||!f){res.writeHead(404);res.end('Not found');return;}try{const b=await readFile(new URL(f,root));res.writeHead(200,{'Content-Type':f.endsWith('.html')?'text/html; charset=utf-8':f.endsWith('.js')?'text/javascript; charset=utf-8':f.endsWith('.json')?'application/json; charset=utf-8':f.endsWith('.png')?'image/png':'text/plain; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});res.end(b);}catch{res.writeHead(404);res.end('Not found');}});
server.listen(0,'127.0.0.1',()=>console.log(`http://127.0.0.1:${server.address().port}/`));
process.on('SIGINT',()=>server.close(()=>process.exit(130)));
