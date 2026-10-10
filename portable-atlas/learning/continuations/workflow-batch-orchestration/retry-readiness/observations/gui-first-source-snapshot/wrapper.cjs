/* Atlas: wrapper for the supplied-page checker; no resource lifecycle. */
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert');
const source=path.resolve(__dirname,'../../../workflow-retry-readiness/check-browser.cjs');
const expected='9aa2c4c2144f341935b65be01d93c7055b99485d58c09ea05e54cec90bf16f7f';
module.exports=async function(options){
 const actual=crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex');assert.equal(actual,expected,'checker body changed before GUI');
 delete require.cache[require.resolve(source)];
 const check=require(source),report=await check(options);
 report.wrapper={file:__filename,sha256:crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex'),body:source,body_sha256:actual,cache_cleared:true};
 fs.writeFileSync(path.join(options.outDir,'report.json'),JSON.stringify(report,null,2)+'\n');return report;
};
