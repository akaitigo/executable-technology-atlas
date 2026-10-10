import http from 'node:http';
import {readFile} from 'node:fs/promises';
const root=new URL('./',import.meta.url);
const allowed=new Map([['/','index.html'],['/index.html','index.html'],['/keyboard.js','keyboard.js'],['/lesson.js','lesson.js'],['/README.md','README.md'],['/scope.json','scope.json']]);
const server=http.createServer(async(req,res)=>{
  const file=allowed.get(req.url);
  if(req.method!=='GET'||!file){res.writeHead(404);res.end('Not found');return;}
  try{const data=await readFile(new URL(file,root));res.writeHead(200,{'Content-Type':file.endsWith('.html')?'text/html; charset=utf-8':file.endsWith('.js')?'text/javascript; charset=utf-8':file.endsWith('.json')?'application/json; charset=utf-8':'text/plain; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});res.end(data);}catch{res.writeHead(404);res.end('Not found');}
});
server.listen(0,'127.0.0.1',()=>console.log(`http://127.0.0.1:${server.address().port}/`));
process.on('SIGINT',()=>server.close(()=>process.exit(130)));
