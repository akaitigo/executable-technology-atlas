#!/usr/bin/env node
import { readdir, readFile, stat, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { gzipSync } from 'node:zlib';
import { performance } from 'node:perf_hooks';
import { route } from './lib/router.mjs';

const root=process.cwd();const chunkDir=path.join(root,'dist/client/_next/static/chunks');const cssDir=path.join(root,'dist/client/_next/static/css');
async function totalGzip(dir){let total=0;for(const name of await readdir(dir)){const file=path.join(dir,name);if((await stat(file)).isFile())total+=gzipSync(await readFile(file)).length;}return total;}
const [jsGzip,cssGzip]=await Promise.all([totalGzip(chunkDir),totalGzip(cssDir)]);
const index=JSON.parse(await readFile(path.join(root,'app/data/index.generated.json'),'utf8'));const samples=[];
for(let i=0;i<1000;i++){const start=performance.now();route(index,{query:i%2?'データ':'security',audience:i%3===0?'operator':undefined});samples.push(performance.now()-start);}
samples.sort((a,b)=>a-b);const searchP95Ms=samples[Math.floor(samples.length*.95)];const budgets={initialJsGzipBytes:174080,cssGzipBytes:51200,searchP95Ms:100};
const metrics={initialJsGzipBytes:jsGzip,cssGzipBytes:cssGzip,searchP95Ms:Number(searchP95Ms.toFixed(3)),subjects:index.subjects.length};
const checks={initialJs:jsGzip<=budgets.initialJsGzipBytes,css:cssGzip<=budgets.cssGzipBytes,search:searchP95Ms<=budgets.searchP95Ms,fixture:index.subjects.length===97};
const report={schemaVersion:1,measuredAt:'2026-08-28T00:00:00Z',budgets,metrics,checks,verdict:Object.values(checks).every(Boolean)?'pass':'fail'};
await mkdir(path.join(root,'evidence/reports'),{recursive:true});await writeFile(path.join(root,'evidence/reports/performance.json'),`${JSON.stringify(report,null,2)}\n`);console.log(`Performance: JS ${Math.round(jsGzip/1024)}KiB gzip / CSS ${Math.round(cssGzip/1024)}KiB gzip / search p95 ${searchP95Ms.toFixed(3)}ms — ${report.verdict}`);if(report.verdict!=='pass')process.exitCode=1;
