import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import wave8References from './local-learning-wave8-references.json' with { type: 'json' };
import wave9References from './local-learning-wave9-references.json' with { type: 'json' };
import wave10References from './local-learning-wave10-references.json' with { type: 'json' };
import wave11References from './local-learning-wave11-references.json' with { type: 'json' };
import wave12References from './local-learning-wave12-references.json' with { type: 'json' };
import wave14References from './local-learning-wave14-references.json' with { type: 'json' };
import wave15References from './local-learning-wave15-references.json' with { type: 'json' };
import wave16References from './local-learning-wave16-references.json' with { type: 'json' };
import wave17References from './local-learning-wave17-references.json' with { type: 'json' };
import wave18References from './local-learning-wave18-references.json' with { type: 'json' };
import wave19References from './local-learning-wave19-references.json' with { type: 'json' };
import wave20References from './local-learning-wave20-references.json' with { type: 'json' };
import wave21References from './local-learning-wave21-references.json' with { type: 'json' };
import wave22References from './local-learning-wave22-references.json' with { type: 'json' };
import wave23References from './local-learning-wave23-references.json' with { type: 'json' };
import wave24References from './local-learning-wave24-references.json' with { type: 'json' };
const reviewedReferences={units:{...wave8References.units,...wave9References.units,...wave10References.units,...wave11References.units,...wave12References.units,...wave14References.units,...wave15References.units,...wave16References.units,...wave17References.units,...wave18References.units,...wave19References.units,...wave20References.units,...wave21References.units,...wave22References.units,...wave23References.units,...wave24References.units}};

import migrationLessons from './migration-lessons.json' with { type: 'json' };
import migrationFiles from './migration-files.json' with { type: 'json' };
export const portalRoot=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');

export const migrationUnits=migrationLessons.units;
const migrationById=new Map(migrationUnits.map(row=>[row.id,row]));
function unitLocation(subject,unit){
  const row=migrationById.get(`${subject}~${unit}`);
  if(!row)throw Error('移行manifest未登録教材');
  return row.location;
}
const publishedByLocation=new Map();
function publishedFiles(location){
  if(!publishedByLocation.has(location))publishedByLocation.set(location,migrationFiles.files.filter(f=>f.path.startsWith(location+'/')).map(f=>f.path.slice(location.length+1)));
  return publishedByLocation.get(location);
}
export function migrationReviewUnits(area){
  const rows=area==='candidate148'?migrationUnits.filter(x=>x.status==='candidate148-only-not-central-accepted'):area==='pending'?migrationUnits.filter(x=>x.status.startsWith('locally-accepted-')):[];
  return rows.map(x=>({...x,accepted:false}));
}
export function migrationNotice(area='formal142'){
 const text=area==='formal142'?'既定：歴史上の中央統合142教材':area==='candidate148'?'別領域：148候補の追加6教材（中央受入前）':'別領域：その他の未統合43教材';
 return `<aside><strong>${text}</strong><p>全191教材の移行レビュー用コピーです。個別受入191・中央統合142・未統合49を保持し、このコピーの動作受入や分野全体の完成を意味しません。私的記録・未検査画像等は非同梱で、保存readerの一部参照は未解消です。元のSHAは過去の原票に属します。</p><nav><a href="/">正式142</a><a href="/review/candidate148">候補の追加6</a><a href="/review/pending">未統合43</a></nav></aside>`;
}

const originals={
  'frontend-behavior':['frontend-behavior-atlas','learning','README.md','layout-min-size.html'],
  flutter:['flutter-reference-atlas','learning/widget-state-lifecycle','README.md',null],
  kotlin:['kotlin-reference-atlas','learning/nullability-diagnostics','README.md','report.html'],
  argocd:['argocd-reference-atlas','learning/reconciliation-drift','README.md','index.html'],
  postgresql:['postgresql-reference-atlas','learning','README.md',null],
  rabbitmq:['rabbitmq-reference-atlas','learning','README.md',null],
  'zero-trust':['zero-trust-reference-atlas','learning','README.md',null],
};
// Only previews exercised through this integrated reader are enabled directly.
const directPreviews=new Set(['relational-database-sql','backend-application-engineering','frontend-behavior','argocd','kotlin']);
// Central acceptance is explicit; finding a directory never promotes it.
export function readAcceptedUnits(catalog,manifestPath=path.join(portalRoot,'app/lib/local-learning-accepted.json')){
  if(fs.realpathSync(manifestPath)!==path.resolve(manifestPath))throw Error('manifest symlinkを拒否');
  const manifest=JSON.parse(fs.readFileSync(manifestPath,'utf8'));
  if(!manifest||Object.keys(manifest).sort().join(',')!=='schemaVersion,units'||manifest.schemaVersion!==1||!Array.isArray(manifest.units))throw Error('受入manifest契約違反');
  const seen=new Set();
  for(const row of manifest.units){
    if(!row||Object.keys(row).sort().join(',')!=='accepted,subject,ui,unit'||row.accepted!==true||!catalog.some(x=>x.id===row.subject)||typeof row.unit!=='string'||!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(row.unit)||!['static','api','unverified'].includes(row.ui))throw Error('未受入・不正metadataを拒否');
    const id=`${row.subject}~${row.unit}`;if(seen.has(id))throw Error('重複受入ID');seen.add(id);
  }
  return manifest.units;
}
export const escapeHtml=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function learningCatalog(root=portalRoot){
  const index=JSON.parse(fs.readFileSync(path.join(root,'app/data/index.generated.json'),'utf8'));
  const rows=[]; // Old management plans are not runtime inputs.
  return index.subjects.map(s=>{
    const row=rows.find(x=>x.split('|')[2].trim()===`\`${s.id}\``);
    const original=originals[s.id];
    const dir=original?path.resolve(root,'..',original[0],original[1]):path.join(root,'learning/subjects',s.id);
    const item={id:s.id,dir,allowedFiles:original?[]:publishedFiles(`learning/subjects/${s.id}`)};
    let boundaryRejected=false,rootReadable=false;
    try{rootReadable=fs.realpathSync(dir)===path.resolve(dir)&&fs.lstatSync(dir).isDirectory();boundaryRejected=!rootReadable;}catch(error){boundaryRejected=error.code!=='ENOENT';}
    const validatedFile=file=>{
      if(!rootReadable)return null;
      try{return resolveLearningFile([item],s.id,file);}catch(error){if(error.code!=='ENOENT')boundaryRejected=true;return null;}
    };
    const readme=original?.[2]??'README.md', screen=original?.[3]??(original?null:'index.html');
    const readmePath=validatedFile(readme),screenPath=screen&&validatedFile(screen),guidePath=validatedFile('LEARNING_PATH.md');
    const text=readmePath?fs.readFileSync(readmePath,'utf8'):'';
    const apiSources=rootReadable?fs.readdirSync(dir).filter(f=>/\.(js|html)$/.test(f)).map(validatedFile).filter(Boolean):[];
    const api=apiSources.some(file=>/fetch\([^\n]*["'`]\/?api(?:[/?"'`])/.test(fs.readFileSync(file,'utf8')));
    return {id:s.id,title:s.title,domain:s.domain,dir,allowedFiles:item.allowedFiles,readme:readmePath?readme:null,screen:screenPath?screen:null,
      guide:guidePath?'LEARNING_PATH.md':null,status:original?'隣接repo（別途配置・内容確認）':'教材コピーあり・移行後未受入',
      accepted:false,
      directPreview:rootReadable&&!boundaryRejected&&directPreviews.has(s.id)&&!api,
      mode:boundaryRejected?'教材path境界を拒否（該当sourceは閲覧不可）':!rootReadable?'教材root未確認（入口不足を保持）':s.id==='flutter'?'Flutter SDK／専用App起動':api?'専用API起動が必要':s.id==='frontend-behavior'?'ブラウザ内の実DOM操作（他の実験は個別手順）':s.id==='argocd'?'説明モデル／Browser内操作（LIVE未実行）':directPreviews.has(s.id)?'保存reader／Browser内操作（再実行は個別手順）':'個別起動（統合portでの操作未確認）',
      location:original?`../${original[0]}/${original[1]}`:`learning/subjects/${s.id}`,
      commands:[...text.matchAll(/```(?:sh|bash|shell)?\n([\s\S]*?)```/g)].map(m=>m[1].trim()), original:Boolean(original)};
  });
}

export function learningRoutes(catalog,root=portalRoot,units=readAcceptedUnits(catalog,path.join(root,'app/lib/local-learning-accepted.json'))){
  // Reading pending work never changes central acceptance. All files are explicitly selected.
  return [...catalog,{id:'software-quality-engineering~qe-reference',title:'QE補助文書',dir:path.join(root,'learning/quality-engineering-atlas'),allowedFiles:publishedFiles('learning/quality-engineering-atlas'),directPreview:false},...migrationUnits.map(row=>({
    id:row.id,title:`有限教材 · ${catalog.find(x=>x.id===row.subject)?.title??row.subject}`,
    dir:path.join(root,row.location),allowedFiles:publishedFiles(row.location),readme:'README.md',screen:publishedFiles(row.location).includes('index.html')?'index.html':null,
    directPreview:row.ui==='static'||row.migrationPreview==='saved',migrationPreview:row.migrationPreview,subject:row.subject,unit:row.unit,accepted:row.status==='formal142-integrated',location:row.location,
    mode:row.ui==='static'||row.migrationPreview==='saved'?'保存reader・移行後GUI未確認':row.ui==='api'?'専用APIが必要・移行後未実行':'source閲覧・個別実行は未確認',
  }))];
}

export function resolveLearningFile(catalog,id,relative,{directory=false}={}){
  const item=catalog.find(x=>x.id===id);if(!item)throw Error('未登録Subject');
  if(item.allowedFiles&&!item.allowedFiles.includes(relative)&&!(directory&&item.allowedFiles.some(f=>f.startsWith(relative.replace(/\/$/,'')+'/'))))throw Error('配送候補の明示file登録外');
  if(directory)relative=relative.replace(/\/$/,'');
  if(!relative||path.isAbsolute(relative)||relative.split('/').some(x=>x==='..'||x.startsWith('.')||!x))throw Error('教材外pathを拒否');
  if(fs.realpathSync(item.dir)!==path.resolve(item.dir))throw Error('symlink rootを拒否');
  let p=item.dir;
  for(const part of relative.split('/')){p=path.join(p,part);if(fs.lstatSync(p).isSymbolicLink())throw Error('symlinkを拒否');}
  if(directory&&fs.statSync(p).isDirectory())return p;
  const reviewed=Object.hasOwn(reviewedReferences.units,item.id)?reviewedReferences.units[item.id]:null;
  const explicitExtra=item.unit==='wal-snapshot-checkpoint'&&(relative==='CURRENT'||/\.(ndjson|wal|sqlite-(wal|shm))$/.test(relative))||item.unit==='undeclared-environment-input'&&/\.bin$/.test(relative)||['ci-cd-release-engineering~rollback-data-compatibility','data-engineering-orchestration~incremental-corrected-batch','sre-incident-operations~multiwindow-burn-alert','media-codec-streaming~riff-chunk-padding','performance-capacity-engineering~two-server-bounded-queue','cloud-architecture~replica-lag-failover-read','software-architecture~runtime-dependency-conformance'].includes(item.id)&&relative==='CURRENT'||reviewed?.currentDirectory&&relative==='CURRENT'||reviewed?.binaryArtifacts?.includes(relative);
  if(!fs.statSync(p).isFile()||(!explicitExtra&&!reviewed?.sourceArtifacts?.includes(relative)&&!/^\.(md|html|js|mjs|css|json|svg|png|jpe?g|gif|webp|py|txt|csv|wav|wasm|sql|sqlite3?|db|kt|java|dart|go|ts|tsx|swift|wgsl|v|c|h|sh|log|zip|pem|cnf)$/.test(path.extname(p))))throw Error('未対応file');
  if(reviewed?.currentDirectory&&relative==='CURRENT'&&fs.readFileSync(p,'utf8').trim()!==reviewed.currentDirectory)throw Error('未検証CURRENT directory');
  if(path.extname(p)==='.pem'&&/PRIVATE KEY/.test(fs.readFileSync(p,'utf8')))throw Error('秘密鍵を拒否');
  return p;
}
export function renderDirectory(catalog,id,relative){
  const dir=resolveLearningFile(catalog,id,relative,{directory:true});
  const entries=fs.readdirSync(dir).flatMap(name=>{try{const p=resolveLearningFile(catalog,id,`${relative.replace(/\/$/,'')}/${name}`,{directory:true}),suffix=fs.statSync(p).isDirectory()?'/':'';return [`<li><a href="${encodeURIComponent(name)}${suffix}">${escapeHtml(name)}${suffix}</a></li>`];}catch{return [];}});
  return page('登録教材の原票directory',`<h1>原票directory（read-only）</h1><p>登録root内の対応fileのみ表示します。commandは実行しません。</p><ul>${entries.join('')}</ul>`);
}
function page(title,body){return `<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>${escapeHtml(title)}</title><style>body{font:17px/1.7 system-ui;margin:auto;max-width:1100px;padding:24px;background:#f7f8fc;color:#172033}a{color:#164aa0}a:focus,summary:focus,input:focus{outline:3px solid #dc6b00}section,article{background:white;padding:20px;margin:16px 0;border:1px solid #ced5e1;border-radius:12px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#edf1f8;padding:12px}input,select{font:inherit;padding:8px;max-width:100%}nav{display:flex;gap:18px;flex-wrap:wrap}small{display:block}h1{font-size:2rem}img{max-width:100%}</style><body><a href="/api/local-learning">教材一覧へ</a>${body}</body></html>`;}
export function renderLearningHome(catalog,units=readAcceptedUnits(catalog),root=portalRoot){
  const topics=units.map(row=>{
    let title='README見出し未確認';
    try{
      if(!catalog.some(x=>x.id===row.subject)||!/^[-a-z0-9]+$/.test(row.subject)||!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(row.unit))throw Error('登録外metadata');
      const item={id:`${row.subject}~${row.unit}`,dir:path.join(root,unitLocation(row.subject,row.unit)),allowedFiles:publishedFiles(unitLocation(row.subject,row.unit))};
      const file=resolveLearningFile([item],item.id,'README.md');
      title=fs.readFileSync(file,'utf8').match(/^# ([^\n\r]+)$/m)?.[1]??title;
    }catch{/* Missing/refused metadata stays visible; never follow a symlink. */}
    return {...row,title};
  });
  const acceptedUnits=Object.fromEntries([...new Set(topics.map(x=>x.subject))].map(subject=>[subject,topics.filter(x=>x.subject===subject)]));
  const domains=[...new Map(catalog.map(x=>[x.domain.id,x.domain.title])).entries()];
  const topicLink=t=>`<span><a href="/lesson/${t.subject}~${t.unit}/README.md" aria-describedby="topic-${t.subject}-${t.unit}">有限深掘り：${escapeHtml(t.title)}</a><small id="topic-${t.subject}-${t.unit}">${escapeHtml(t.unit)}</small></span>`;
  const card=x=>`<article data-search="${escapeHtml(`${x.id} ${x.title} ${x.domain.title} ${(acceptedUnits[x.id]??[]).map(t=>`${t.unit} ${t.title}`).join(' ')}`.toLowerCase())}" data-domain="${x.domain.id}"><h2>${escapeHtml(x.title)}</h2><small>${escapeHtml(x.id)} · ${escapeHtml(x.domain.title)}</small><p>${x.readme?'入口コピーあり・移行後未受入':x.original?'隣接repoにある入口':'入口コピー未確認'} · 分野全体は未完</p><p>${escapeHtml(x.mode)}${x.original?' · sibling Repositoryのローカル教材':''}</p><nav>${x.readme?`<a href="/lesson/${x.id}/${x.readme}">前提・操作・原票・実装・次実験を読む</a>`:'<span>README未確認（入口不足を保持）</span>'}${x.guide?`<a href="/lesson/${x.id}/${x.guide}">深掘りの読み順</a>`:''}${x.screen?`<a href="/lesson/${x.id}/${x.screen}">${!x.directPreview?'画面sourceを読む（操作は個別起動）':'教材画面を開く'}</a>`:''}${(acceptedUnits[x.id]??[]).map(topicLink).join('')}</nav>${x.commands.length?`<details><summary>個別起動・検査コマンドを読む（実行ボタンなし）</summary><p>Portal rootからの作業場所：<code>${escapeHtml(x.location)}</code>。この教材READMEのdirectoryを作業場所とする抜粋です。前提・書込／記録・port・cleanupの条件はREADME全文を確認してください。</p><pre>${escapeHtml(x.commands.join('\n\n'))}</pre></details>`:''}</article>`;
  return page('Macローカル教材',`<h1>Macローカル教材</h1><p>前提 → 予想 → 操作 → 正常／異常比較 → 原典・実装・原票 → 次実験の順に進みます。</p><section><h2>最初に読む</h2><p>${catalog.length}分野の入口を表示します。隣接repoの入口と移行後未受入の教材も一覧に残します。分野全体の完成は判定していません。入口教材が揃っていても、分野全体の網羅を示すものではありません。</p><p>保存readerは過去の観測を閲覧します。専用Python API、Flutter等は各READMEの前提とコマンドで別terminal・別portに起動してください。このreaderはAPIやcommandを実行しません。一括setupはありません。</p><p>原票や実装リンクはread-onlyです。README中の記録commandは新しい実験であり、閲覧だけなら実行不要です。未教材範囲・次実験は未実行計画のままです。</p></section><label>分野・題材を探す <input id="search" type="search"></label> <label>領域 <select id="domain"><option value="">全領域</option>${domains.map(([id,title])=>`<option value="${id}">${escapeHtml(title)}</option>`).join('')}</select></label><p id="results" role="status" aria-live="polite">${catalog.length}件表示</p><div id="cards">${catalog.map(card).join('')}</div><script>const q=document.querySelector('#search'),d=document.querySelector('#domain');function filter(){let n=0;document.querySelectorAll('article').forEach(a=>{a.hidden=!(a.dataset.search.includes(q.value.toLowerCase())&&(!d.value||a.dataset.domain===d.value));if(!a.hidden)n++});document.querySelector('#results').textContent=n+'件表示（絞り込みは完成判定ではありません）'}q.oninput=filter;d.onchange=filter;</script>`);
}
const viewerReferences={
  'analytics-data-platform~as-of-dimension-history':{
    'README.md':['analytics-data-platform~as-of-dimension-history','README.md'],
    'model.py':['analytics-data-platform~as-of-dimension-history','model.py'],
    'oracle.py':['analytics-data-platform~as-of-dimension-history','oracle.py'],
    'observations/attempt-01/raw.json':['analytics-data-platform~as-of-dimension-history','observations/attempt-01/raw.json'],
    '../../../subjects/analytics-data-platform/README.md':['analytics-data-platform','README.md'],
    '../../../subjects/relational-database-sql/README.md':['relational-database-sql','README.md'],
  },
  'software-maintenance-migration~expand-contract-client-coexistence':{
    'README.md':['software-maintenance-migration~expand-contract-client-coexistence','README.md'],
    'model.py':['software-maintenance-migration~expand-contract-client-coexistence','model.py'],
    'oracle.py':['software-maintenance-migration~expand-contract-client-coexistence','oracle.py'],
    'observations/attempt-02/raw.json':['software-maintenance-migration~expand-contract-client-coexistence','observations/attempt-02/raw.json'],
    '../../../subjects/software-maintenance-migration/README.md':['software-maintenance-migration','README.md'],
    '../../../subjects/ci-cd-release-engineering/README.md':['ci-cd-release-engineering','README.md'],
  },
  'information-retrieval-search~precision-recall-contract':{
    '../../../subjects/information-retrieval-search/README.md':['information-retrieval-search','README.md'],
    '../../../subjects/generative-ai-rag/README.md':['generative-ai-rag','README.md'],
  },
  'real-time-safety-critical~priority-inheritance-blocking':{
    '../../../subjects/real-time-safety-critical/README.md':['real-time-safety-critical','README.md'],
    '../../formal-methods-verification/two-lock-deadlock-livelock/README.md':['formal-methods-verification~two-lock-deadlock-livelock','README.md'],
  },
};
const frontendViewerId='frontend-application-architecture~selection-draft-cancel';
const frontendViewerFiles=['README.md','EXPECTATIONS.md','app.js','oracle.json','oracle.py','SOURCES.md','evidence/current.json'];
export function isExactLearningViewer(id,relative){
  return (id===frontendViewerId&&relative==='document.html')
    || (Object.hasOwn(reviewedReferences.units,id)&&(reviewedReferences.units[id].viewer===relative||relative==='reference'&&Boolean(reviewedReferences.units[id].serverReferences)))
    || (['analytics-data-platform~as-of-dimension-history','software-maintenance-migration~expand-contract-client-coexistence'].includes(id)&&relative==='source.html');
}
const capacityId='performance-capacity-engineering~two-server-bounded-queue';
const capacityRawTargets=[['performance-capacity-engineering','README.md'],['sre-incident-operations~multiwindow-burn-alert','README.md'],[capacityId,'README.md'],[capacityId,'COVERAGE.md']];
const inlineRawReferences={
  ...Object.fromEntries(Object.entries(reviewedReferences.units).filter(([,value])=>value.inlineRawTargets).map(([id,value])=>[id,value.inlineRawTargets])),
  [capacityId]:capacityRawTargets,
  'cloud-architecture~replica-lag-failover-read':[
    ['cloud-architecture','README.md'],['database-engine-internals~wal-snapshot-checkpoint','README.md'],
    ['cloud-architecture~replica-lag-failover-read','README.md'],['cloud-architecture~replica-lag-failover-read','COVERAGE.md'],
  ],
  'software-architecture~runtime-dependency-conformance':[
    ['software-architecture','README.md'],['cloud-architecture~replica-lag-failover-read','README.md'],
    ['software-architecture~runtime-dependency-conformance','README.md'],['software-architecture~runtime-dependency-conformance','COVERAGE.md'],
  ],
};
export function learningViewerReference(routes,id,relative,search){
  const query=new URLSearchParams(search);
  if([...query.keys()].length!==1||!query.has('file'))return null;
  const reviewed=Object.hasOwn(reviewedReferences.units,id)?reviewedReferences.units[id]:null;
  if(reviewed&&(relative===reviewed.viewer||relative==='reference'&&reviewed.serverReferences)){
    const references=relative==='reference'?reviewed.serverReferences:reviewed.references;
    if(!references||!Object.hasOwn(references,query.get('file')))return null;
    const [targetId,file]=references[query.get('file')];
    const resolved=resolveLearningFile(routes,targetId,file);
    return {id:targetId,file,resolved,url:`/lesson/${targetId}/${file}`};
  }
  if(id===frontendViewerId&&relative==='document.html'){
    const file=query.get('file');
    if(!frontendViewerFiles.includes(file))return null;
    const resolved=resolveLearningFile(routes,id,file);
    return {id,file,resolved,url:`/lesson/${id}/${file}`};
  }
  if(relative!=='source.html')return null;
  if(!Object.hasOwn(viewerReferences,id))return null;
  const references=viewerReferences[id];
  if(!Object.hasOwn(references,query.get('file')))return null;
  const target=references[query.get('file')];
  const [targetId,file]=target;
  const resolved=resolveLearningFile(routes,targetId,file);
  return {id:targetId,file,resolved,url:`/lesson/${targetId}/${file}`};
}
export function learningBinaryReference(id,relative){
  // Only the reviewed candidate109 saved gzip/tar paths gain binary responses.
  // Never generalize gzip handling or decompress/execute the stored artifact.
  const reviewed=Object.hasOwn(wave17References.units,id)?wave17References.units[id]:null;
  return Boolean(reviewed?.binaryArtifacts?.includes(relative));
}
export function learningRawReference(id,relative,search){
  const reviewed=Object.hasOwn(reviewedReferences.units,id)?reviewedReferences.units[id]:null;
  return search===''&&Boolean(reviewed?.rawFetchTargets?.includes(relative))
    || search==='?raw=1'&&Object.values(inlineRawReferences).some(targets=>targets.some(([target,file])=>id===target&&relative===file));
}
const kotlinDocumentSnapshots=[
  'observations/operational-revision-20261006T054006019240Z/before/current-docs/',
  'browser-qa/gui-revision-20261006T060214056778Z/before/',
];
export function learningDocumentSnapshotRoot(id,relative){
  const roots=id==='kotlin~smart-cast-boundaries'?kotlinDocumentSnapshots:(Object.hasOwn(reviewedReferences.units,id)?reviewedReferences.units[id].documentSnapshots:[])??[];
  return roots.find(root=>relative.startsWith(root))??null;
}
function documentSnapshotNotice(context){
  return learningDocumentSnapshotRoot(context?.id,context?.relative??'')?'<aside><strong>保存当時の文書snapshot</strong><p>この保存集合は当時の教材全体ではありません。同梱した文書・原票を読み、未同梱の当時参照は元のpathを表示します。現行の同名資料への差替えは行いません。過去のHTMLもsourceとして表示し、操作は実行しません。</p></aside>':'';
}
export function localLearningLink(routes,id,relative,href){
  if(href==='data:,')return href; // Empty favicon, not arbitrary data URLs.
  if(/^(https?:|mailto:|#)/.test(href))return href;
  const snapshotRoot=learningDocumentSnapshotRoot(id,relative);
  if(snapshotRoot){
    const item=routes.find(route=>route.id===id);
    const snapshotDir=path.resolve(item.dir,snapshotRoot);
    const target=path.resolve(path.dirname(path.join(item.dir,relative)),decodeURIComponent(href.split(/[?#]/)[0]));
    if(!target.startsWith(snapshotDir+path.sep))throw Error('保存snapshotに未同梱の当時参照');
    try{resolveLearningFile(routes,id,path.relative(item.dir,target));}
    catch{throw Error('保存snapshotに未同梱の当時参照');}
  }
  const contract=Object.hasOwn(reviewedReferences.units,id)?reviewedReferences.units[id]:null;
  // Auxiliary source documents retain their original scope, never the current
  // lesson's same-named files. Only exact reviewed document+href pairs are bound.
  if(contract?.auxiliaryFiles?.includes(relative))throw Error('補助原資料に属する未移入参照');
  const aliases=contract?.documentAliases;
  if(!snapshotRoot&&aliases&&Object.hasOwn(aliases,relative)&&Object.hasOwn(aliases[relative],href)){
    const file=aliases[relative][href];resolveLearningFile(routes,id,file);
    return `/lesson/${id}/${file.split('/').map(encodeURIComponent).join('/')}`;
  }
  const routeAliases=contract?.routeAliases;
  if(!snapshotRoot&&routeAliases&&Object.hasOwn(routeAliases,relative)&&Object.hasOwn(routeAliases[relative],href)){
    const target=routeAliases[relative][href];
    const file=resolveLearningFile(routes,target.id,target.file);
    if(createHash('sha256').update(fs.readFileSync(file)).digest('hex')!==target.sha256)throw Error('固定前提reader digest不一致');
    return `/lesson/${target.id}/${target.file.split('/').map(encodeURIComponent).join('/')}`;
  }

  const viewerUrl=new URL(href,'http://localhost/');
  if(['source.html','document.html','reference','/reference'].includes(href.split(/[?#]/)[0])){
    const reference=learningViewerReference(routes,id,href.split(/[?#]/)[0].replace(/^\//,''),viewerUrl.search);
    if(reference)return reference.url;
  }
  // Only the two reviewed dedicated JS servers have these exact first-unit aliases.
  const referenceSubject={'algorithms-data-structures~bfs-dfs-shortest-paths':'algorithms-data-structures','information-theory-coding~crc-undetected-errors':'information-theory-coding'}[id];
  if(referenceSubject&&['reference/README.md','reference/LEARNING_PATH.md'].includes(href)){
    const target=href.slice('reference/'.length);resolveLearningFile(routes,referenceSubject,target);
    return `/lesson/${referenceSubject}/${target}`;
  }
  // The independent Kotlin pilot is not registered by this alias. Its copied
  // prerequisite retains a different original document scope, never pilot files.
  if(id==='kotlin~smart-cast-boundaries'){
    if(relative==='references/kotlin-null-operators-README.md')throw Error('元単元に属する未移入参照');
    if(relative==='README.md'&&href==='../kotlin-null-operators/README.md'){
      resolveLearningFile(routes,id,'references/kotlin-null-operators-README.md');
      return `/lesson/${id}/references/kotlin-null-operators-README.md`;
    }
  }
  const item=routes.find(x=>x.id===id);
  const url=new URL(href,'http://localhost/');
  const target=path.resolve(path.dirname(path.join(item.dir,relative)),decodeURIComponent(href.split(/[?#]/)[0]));
  const found=routes.find(x=>target.startsWith(`${x.dir}/`)&&(!x.allowedFiles||x.allowedFiles.includes(path.relative(x.dir,target))));
  if(!found)throw Error('未登録rootへのlink');
  const targetFile=path.relative(found.dir,target);
  resolveLearningFile(routes,found.id,targetFile,{directory:href.split(/[?#]/)[0].endsWith('/')});
  if(Object.hasOwn(inlineRawReferences,id)&&relative==='index.html'&&inlineRawReferences[id].some(([targetId,file])=>found.id===targetId&&targetFile===file)){
    resolveLearningFile(routes,found.id,targetFile);
    // The frozen reader binds its inline handler to hrefs ending in .md.
    // A fragment preserves that selector while fetch excludes the fragment.
    return `/lesson/${found.id}/${targetFile}?raw=1#${targetFile}`;
  }
  return `/lesson/${found.id}/${path.relative(found.dir,target).split('/').map(encodeURIComponent).join('/')}${href.split(/[?#]/)[0].endsWith('/')?'/':''}${url.search}${url.hash}`;
}
export function learningCurrentRawNavigation(text,context){
  const contract=Object.hasOwn(reviewedReferences.units,context?.id)?reviewedReferences.units[context.id]:null;
  const reviewed=contract?.currentPointers?.[context.relative]??(context?.relative==='evidence/current.json'?contract?.currentRaw:null);
  if(!reviewed&&(context?.id!==frontendViewerId||context.relative!=='evidence/current.json'))return '';
  const pointer=JSON.parse(text);
  const raw=reviewed?.raw??'run-20261005T130343-2b38da2a.json';
  const digest=reviewed?.sha256??'4d6181c3acc98d61aa1f449da19a9d3fd6332ba869deaeb175bd8f1277d2ca5a';
  if(!pointer||Object.keys(pointer).sort().join(',')!=='raw,sha256'||typeof pointer.raw!=='string'||!/^run-[0-9TZ]+-[0-9a-f]{8}\.json$/.test(pointer.raw)||pointer.raw!==raw||pointer.sha256!==digest)throw Error('未検証current pointer');
  const file=resolveLearningFile(context.routes,context.id,'evidence/'+pointer.raw);
  if(createHash('sha256').update(fs.readFileSync(file)).digest('hex')!==digest)throw Error('current raw digest不一致');
  return `<nav><a href="/lesson/${context.id}/evidence/${raw}">${reviewed?'固定実行raw':'実Browser raw'}（保存原票・再実行なし）</a></nav>`;
}
export function renderSource(text,title,context){return page(title,`<h1>原票・実装source（read-only）</h1><p>表示だけでcommandは実行しません。保存原票の閲覧は新しい実行証拠ではありません。</p>${documentSnapshotNotice(context)}${(()=>{try{return learningCurrentRawNavigation(text,context);}catch{return '<p>過去原票の完全bindingはこの選別コピーでは未再現です。私的保全manifestで元SHAを照合してください。</p>';}})()}<pre><code>${escapeHtml(text)}</code></pre>`);}
// Code notation may look like Markdown links. Share token precedence with the
// source-link auditor so neither layer invents a file from a literal code span.
const markdownInlineTokens=/`[^`]+`|(!?)\[([^\]]+)\]\(([^)]+)\)/g;
export function learningMarkdownLinks(text){
  const links=[];let code=false;
  for(const line of text.split('\n')){
    if(line.startsWith('```')){code=!code;continue;}
    if(code)continue;
    for(const token of line.matchAll(markdownInlineTokens)){
      if(token[3]!==undefined)links.push({image:token[1]==='!',label:token[2],href:token[3]});
    }
  }
  return links;
}
export function renderMarkdown(text,title,context){
  const inline=s=>{
    let out='',offset=0;
    for(const token of s.matchAll(markdownInlineTokens)){
      out+=escapeHtml(s.slice(offset,token.index));offset=token.index+token[0].length;
      if(token[3]===undefined){out+=`<code>${escapeHtml(token[0].slice(1,-1))}</code>`;continue;}
      const image=token[1],label=escapeHtml(token[2]);let url=token[3];
      if(context){try{url=localLearningLink(context.routes,context.id,context.relative,url);}catch{
        out+=learningDocumentSnapshotRoot(context.id,context.relative)?`${label}（保存snapshotに未同梱の当時参照：<code>${escapeHtml(url)}</code>）`:`${label}（reader外参照：<code>${escapeHtml(url)}</code>。元Repositoryで確認）`;continue;
      }}
      out+=/^(?:https?:\/\/|\/lesson\/|#|[a-zA-Z0-9_.][^:]*$)/.test(url)?image?`<img src="${escapeHtml(url)}" alt="${label}" loading="lazy">`:`<a href="${escapeHtml(url)}">${label}</a>`:label;
    }
    return out+escapeHtml(s.slice(offset));
  };
  let code=false,table=false,list=false;const parts=[];
  for(const l of text.split('\n')){
    if(l.startsWith('```')){if(list){parts.push('</ul>');list=false;}code=!code;parts.push(code?'<pre><code>':'</code></pre>');continue;}
    if(code){parts.push(escapeHtml(l)+'\n');continue;}
    if(l.startsWith('|')){if(!table){parts.push('<div style="overflow-x:auto"><table border="1" cellpadding="8">');table=true;}if(!/^\|[\s:|-]+\|$/.test(l))parts.push('<tr>'+l.split('|').slice(1,-1).map(c=>`<td>${inline(c.trim())}</td>`).join('')+'</tr>');continue;}
    if(table){parts.push('</table></div>');table=false;}
    const li=l.match(/^(?:- |\d+\. )(.*)/);if(li){if(!list){parts.push('<ul>');list=true;}parts.push(`<li>${inline(li[1])}</li>`);continue;}
    if(list){parts.push('</ul>');list=false;}
    const h=l.match(/^(#{1,6}) (.*)/);parts.push(h?`<h${h[1].length} id="${escapeHtml(h[2].toLowerCase().replace(/[^\p{L}\p{N}\s-]/gu,'').replace(/\s+/g,'-'))}">${inline(h[2])}</h${h[1].length}>`:`<p>${inline(l)}</p>`);
  }
  if(table)parts.push('</table></div>');if(list)parts.push('</ul>');if(code)parts.push('</code></pre>');const body=parts.join('');
  const item=context?.routes.find(x=>x.id===context.id);
  const base=item?.subject&&context.routes.find(x=>x.id===item.subject);
  const readingOrder=base?`<nav>${base.readme?`<a href="/lesson/${base.id}/${base.readme}">第1教材へ（前提の読み直し）</a>`:'<span>第1教材README未確認</span>'}${base.guide?`<a href="/lesson/${base.id}/${base.guide}">分野の読み順・未教材</a>`:'<span>分野の学習path未確認</span>'}</nav>`:'';
  const followUps=item&&!item.subject&&context.relative===item.readme?context.routes.filter(route=>route.subject===item.id):[];
  const continuationNav=followUps.length?`<section><h2>この前提から進む有限後続教材</h2><p>元文書の「未実施」は記録当時の計画です。後続の有限範囲・起動方式・未確認を個別に確認してください。分野全体の完成へ読み替えません。</p><ul>${followUps.map(route=>{
    let title='README題名未確認（読取拒否を保持）';
    try{title=fs.readFileSync(resolveLearningFile(context.routes,route.id,route.readme),'utf8').match(/^# ([^\n\r]+)$/m)?.[1]??title;}catch{/* Refused metadata stays visible, never read through a symlink. */}
    return `<li><a href="/lesson/${route.id}/${route.readme}">${escapeHtml(title)}</a> · ${escapeHtml(route.mode)}</li>`;
  }).join('')}</ul></section>`:'';
  const entry=item&&context.relative===item.readme?`<section><p>${escapeHtml(item.mode)} · 分野全体は未完</p>${readingOrder}${item.location?`<p>Portal rootからの教材directory：<code>${escapeHtml(item.location)}</code>。実行する場合はREADME全文の前提とcleanupを確認してください。</p>`:''}${item.screen?`<a href="/lesson/${item.id}/${item.screen}">${item.directPreview?'保存教材画面を開く':'画面sourceを読む（操作は個別起動）'}</a>`:''}</section>`:'';
  return page(title,`<p>教材文書reader：コマンドは表示のみ。個別の前提・起動法と未教材を確認してください。</p>${documentSnapshotNotice(context)}${entry}${continuationNav}${body}`);
}
export function rewriteLearningHtml(text,context){
  // Never rewrite template strings in scripts or historical path metadata.
  return text.split(/(<script\b[^>]*>[\s\S]*?<\/script>|<!--[\s\S]*?-->)/gi).map(part=>{
    if(/^<script\b|^<!--/i.test(part))return part;
    return part.replace(/<(?:a|img|link|iframe|audio|video|source)\b[^>]*>/gi,tag=>tag.replace(/(href|src)="([^"]+)"/g,(_,attr,href)=>`${attr}="${escapeHtml((()=>{try{return localLearningLink(context.routes,context.id,context.relative,href.replace(/&amp;/g,'&'));}catch{return '/omitted-reference';}})())}"`));
  }).join('');
}
