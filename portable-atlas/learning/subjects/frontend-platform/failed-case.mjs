const id=new URLSearchParams(location.search).get('case');
const target=id==='loading'?'./missing-module.mjs':id==='syntax'?'./bad-syntax.mjs':null;
const startedAt=new Date().toISOString();
document.getElementById('title').textContent=id==='loading'?'読込失敗: module URLが404':'構文失敗: 200で届いたmoduleがparse不能';
if(!target)throw Error('unknown isolated fixture');
let result;
try{await import(target);result={failed:false};}
catch(error){result={failed:true,name:error.name,message:error.message};}
// A separate HTTP probe makes the HTTP observation explicit; its status is not
// fabricated from the dynamic-import error text.
const response=await fetch(target);
const http={status:response.status,contentType:response.headers.get('content-type')};
const sources=await (await fetch('sources.json')).json();
const raw={kind:'actual-browser-isolated-module-failure',caseId:id,input:target,startedAt,completedAt:new Date().toISOString(),result,http,sourceHashes:sources.sourceHashes,environment:{userAgent:navigator.userAgent,language:navigator.language}};
document.getElementById('status').textContent=`観測完了: ${result.name||'成功'} / 別HTTP probe ${http.status}`;
document.getElementById('error').textContent=JSON.stringify({result,http},null,2);
document.getElementById('raw').textContent=JSON.stringify(raw);
