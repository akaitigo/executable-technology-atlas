#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

export function parseLsofRecords(output) {
  const records=[];
  let current=null;
  for (const line of output.split(/\r?\n/)) {
    if (!line) continue;
    const field=line[0];
    const value=line.slice(1);
    if (field==='p') {
      if (current) records.push(current);
      current={pid:value,command:null,address:null};
    } else if (current&&field==='c') current.command=value;
    else if (current&&field==='n') current.address=value;
  }
  if (current) records.push(current);
  return records;
}

export function verifyLoopbackRecords(records,{host='127.0.0.1',port=4173}={}) {
  const expected=`${host}:${port}`;
  const errors=[];
  if (records.length===0) errors.push(`TCP ${port} にLISTEN中のPortal processがありません`);
  for (const record of records) {
    if (!/^\d+$/.test(record.pid??'')) errors.push('listener PIDを検証できません');
    if (record.address!==expected) errors.push(`許可されないbind address: ${record.address??'missing'}（expected ${expected}）`);
  }
  return {ok:errors.length===0,expected,listeners:records,errors};
}

export function inspectLoopbackListener({host='127.0.0.1',port=4173}={}) {
  const result=spawnSync('lsof',['-nP','-a',`-iTCP:${port}`,'-sTCP:LISTEN','-Fpcn'],{encoding:'utf8'});
  if (result.error) return {ok:false,expected:`${host}:${port}`,listeners:[],errors:[`lsofを実行できません: ${result.error.message}`]};
  if (result.status!==0&&result.status!==1) return {ok:false,expected:`${host}:${port}`,listeners:[],errors:[`lsofがexit ${result.status}: ${result.stderr.trim()}`]};
  return verifyLoopbackRecords(parseLsofRecords(result.stdout),{host,port});
}

if (import.meta.url===pathToFileURL(process.argv[1]).href) {
  const report=inspectLoopbackListener();
  process.stdout.write(`${JSON.stringify(report,null,2)}\n`);
  process.exitCode=report.ok?0:1;
}
