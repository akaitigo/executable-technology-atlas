import http from 'node:http';import {readFile} from 'node:fs/promises';
const root=new URL('./',import.meta.url);http.createServer(async(req,res)=>{try{let path=new URL(req.url,'http://localhost').pathname.slice(1)||'index.html';let data;
if(path==='reference')data=await readFile(new URL('../../../subjects/game-engine-interactive-simulation/README.md',root));
else{if(path.includes('..')||!/^([\w-]+\/)*[\w.-]+$/.test(path))throw Error('PATH');data=await readFile(new URL(path,root));}
res.writeHead(200,{'Content-Type':path.endsWith('.mjs')?'text/javascript':path.endsWith('.html')?'text/html; charset=utf-8':path.endsWith('.json')?'application/json':'text/plain; charset=utf-8','Cache-Control':'no-store'});res.end(data);
}catch(e){res.writeHead(404);res.end('not found');}}).listen(0,'127.0.0.1',function(){console.log(JSON.stringify({url:`http://127.0.0.1:${this.address().port}`,pid:process.pid}));});
