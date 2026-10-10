import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { learningCatalog,learningRoutes,readAcceptedUnits,resolveLearningFile,renderLearningHome,renderMarkdown,renderDirectory,rewriteLearningHtml,renderSource,learningViewerReference,learningRawReference,learningBinaryReference,isExactLearningViewer,learningDocumentSnapshotRoot,migrationNotice,migrationReviewUnits } from './local-learning.mjs';
function withMigrationNotice(text,item){
  const notice=migrationNotice(item.accepted?'formal142':item.location.includes('/candidate148/')?'candidate148':'pending');
  if(/<body\b/i.test(text))return text.replace(/<body([^>]*)>/i,'<body$1>'+notice);
  if(/<\/(?:head)>/i.test(text))return text.replace(/<\/head>/i,'</head><body>'+notice);
  if(/<(?:main|header|h1|section)\b/i.test(text))return text.replace(/(<(?:main|header|h1|section)\b)/i,notice+'$1');
  return notice+text;
}
export function localReaderHandler(req,res,{manifestPath}={}){
  res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Cache-Control','no-store');res.setHeader('Cross-Origin-Resource-Policy','same-origin');
  res.setHeader('X-Frame-Options','DENY');res.setHeader('Content-Security-Policy',"frame-ancestors 'none'; base-uri 'none'; object-src 'none'");
  if(!/^(127\.0\.0\.1|localhost):\d+$/.test(req.headers.host??'')||(req.headers.origin&&req.headers.origin!==`http://${req.headers.host}`)){res.writeHead(403);res.end('loopback same-originのみ');return;}
  if(req.method!=='GET'){res.writeHead(405);res.end('read-only GETのみ');return;}
  try{
    const catalog=learningCatalog(),units=readAcceptedUnits(catalog,manifestPath),routes=learningRoutes(catalog,undefined,units),u=new URL(req.url,'http://localhost');
    if(['/', '/api/local-learning','/review/candidate148','/review/pending'].includes(u.pathname)){
      const area=u.pathname.startsWith('/review/')?u.pathname.split('/')[2]:'formal142';
      res.setHeader('Content-Type','text/html; charset=utf-8');
      res.end(renderLearningHome(catalog,area==='formal142'?units:migrationReviewUnits(area)).replace('<body>','<body>'+migrationNotice(area)));return;
    }
    if(u.pathname==='/omitted-reference'){res.writeHead(410,{'Content-Type':'text/plain; charset=utf-8'});res.end('この参照は配送候補に含めていません。原票は元の私的作業領域に保持しています。代替証拠への差替えはありません。');return;}
    const match=decodeURIComponent(u.pathname).match(/^\/lesson\/([^/]+)\/(.+)$/);if(!match)throw Error('個別起動が必要');
    const sourceFiles={
      'algorithms-data-structures~bfs-dfs-shortest-paths':['cases.json','search.mjs','oracle.mjs','sources.mjs','verify.mjs','check.mjs','serve.mjs','lesson.mjs','index.html','styles.css','scope.json','skills/atlas-bfs-dfs-paths/SKILL.md'],
      'information-theory-coding~crc-undetected-errors':['contract.json','cases.json','crc.mjs','oracle.mjs','sources.mjs','verify.mjs','check.mjs','serve.mjs','lesson.mjs','index.html','styles.css','scope.json','skills/atlas-crc-undetected-errors/SKILL.md'],
    }[match[1]];
    if(sourceFiles&&match[2]==='sources.json'){
      // Dedicated server metadata parity: hashes of actual registered files, never a command run.
      const sourceHashes=Object.fromEntries(sourceFiles.map(name=>[name,createHash('sha256').update(fs.readFileSync(resolveLearningFile(routes,match[1],name))).digest('hex')]));
      res.setHeader('Content-Type','application/json');res.end(JSON.stringify({sourceHashes}));return;
    }
    if(match[2].endsWith('/')){res.setHeader('Content-Type','text/html; charset=utf-8');res.end(renderDirectory(routes,match[1],match[2]));return;}
    const item=routes.find(x=>x.id===match[1]);
    if(!item)throw Error('未登録教材');
    const directPreview=item.directPreview&&!learningDocumentSnapshotRoot(item.id,match[2])&&!(item.migrationPreview==='saved'&&match[2]==='native.html');
    const reference=learningViewerReference(routes,item.id,match[2],u.search);
    if(reference){
      res.setHeader('Content-Type','text/html; charset=utf-8');
      const target=routes.find(x=>x.id===reference.id);
      const text=fs.readFileSync(reference.resolved,'utf8');
      const referenceContext={routes,id:target.id,relative:reference.file};
      res.end(path.extname(reference.file)==='.md'?renderMarkdown(text,target.title,referenceContext):renderSource(text,target.title,referenceContext));return;
    }
    if(isExactLearningViewer(item.id,match[2]))throw Error('未登録viewer参照を拒否');
    const file=resolveLearningFile(routes,match[1],match[2]),ext=path.extname(file);
    if(learningRawReference(item.id,match[2],u.search)){
      res.setHeader('Content-Type','text/plain; charset=utf-8');res.end(fs.readFileSync(file));return;
    }
    const types={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.gif':'image/gif','.webp':'image/webp','.wasm':'application/wasm','.wav':'audio/wav','.sqlite':'application/octet-stream','.db':'application/octet-stream'};
    res.setHeader('Content-Type',ext==='.md'?'text/html; charset=utf-8':(ext==='.html'&&!directPreview)||(ext==='.json'&&req.headers.accept?.includes('text/html'))?'text/plain; charset=utf-8':ext==='.sqlite3'?'application/octet-stream':types[ext]??'text/plain; charset=utf-8');
    const context={routes,id:item.id,relative:match[2]};
    const binary=/^\.(wal|sqlite-(wal|shm)|bin|tar)$/.test(ext)||learningBinaryReference(item.id,match[2]);
    if(binary)res.setHeader('Content-Type','application/octet-stream');
    const sourceNavigation=!binary&&req.headers.accept?.includes('text/html')&&ext!=='.md'&&!(ext==='.html'&&directPreview)&&!/^\.(png|jpe?g|gif|webp|wav|wasm|sqlite3?|db|zip)$/.test(ext);
    if(sourceNavigation){res.setHeader('Content-Type','text/html; charset=utf-8');res.end(renderSource(fs.readFileSync(file,'utf8'),item.title,context));return;}
    if(item.id==='workflow-batch-orchestration~retry-readiness'&&match[2]==='reader-app.js'){
      // Portal presentation revision; imported original and historical source views remain intact.
      const original=fs.readFileSync(file,'utf8');
      const oldLabel="\u3053\u306e\u5883\u754c\u3067\u5224\u5b9a\u3057\u305f\u6642\u523b",newLabel="\u3053\u306e\u5883\u754c\u3067\u7167\u5408\u3057\u305f\u518d\u958b\u6642\u523b\uff08due\uff09";
      if(createHash('sha256').update(original).digest('hex')!=='29b98fe9664b5c23d4d46b16759774fff494697d398be0277fb5970c4547030e'||original.split(oldLabel).length!==2)throw Error('retry due-label revision source mismatch');
      res.setHeader('X-Atlas-Presentation-Revision','retry-due-label-v1');
      res.end(original.replace(oldLabel,newLabel));return;
    }
    res.end(ext==='.md'?renderMarkdown(fs.readFileSync(file,'utf8'),item.title,context):ext==='.html'&&directPreview?withMigrationNotice(rewriteLearningHtml(fs.readFileSync(file,'utf8'),context),item):fs.readFileSync(file));
  }catch{res.writeHead(404,{'Content-Type':'text/plain; charset=utf-8'});res.end('未対応・教材外path。登録教材READMEから個別起動法を確認してください。');}
}
