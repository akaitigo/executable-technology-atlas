/* Atlas: root-owned existing-page adapter; no lifecycle operations. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
module.exports=async function(args){
 const source=path.resolve(__dirname,'../../../quantum-partial-dephasing/check-browser.cjs');
 const sha=f=>crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
 const binding={wrapper:{path:__filename,sha256:sha(__filename)},lesson_checker:{path:source,sha256:sha(source)}};
 delete require.cache[require.resolve(source)];
 const checker=require(source);const report=await checker(args);report.entry_sources=binding;
 report.entry_sources_unchanged=binding.wrapper.sha256===sha(__filename)&&binding.lesson_checker.sha256===sha(source);
 if(!report.entry_sources_unchanged){report.passed=false;report.errors.push({kind:'entry-source-changed'});}
 fs.writeFileSync(path.join(args.outDir,'report.json'),JSON.stringify(report,null,2)+'\n');return report;
};
