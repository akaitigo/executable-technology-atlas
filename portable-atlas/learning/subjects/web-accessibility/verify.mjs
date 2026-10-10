import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import keyboard from './keyboard.js';
const root=path.dirname(fileURLToPath(import.meta.url));
const sources=['index.html','keyboard.js','lesson.js','verify.mjs','serve.mjs','scope.json','package.json'];
const hash=b=>createHash('sha256').update(b).digest('hex');
const digests=Object.fromEntries(await Promise.all(sources.map(async f=>[f,hash(await readFile(path.join(root,f)))])));
// Independent expected table: no use of the lesson's counters or event reducer.
const fixtures=[
  [false,{type:'keydown',key:'Enter',repeat:false,focused:true,disabled:false},{armed:false,activate:true,prevent:true}],
  [false,{type:'keydown',key:'Enter',repeat:true,focused:true,disabled:false},{armed:false,activate:false,prevent:true}],
  [false,{type:'keydown',key:' ',repeat:false,focused:true,disabled:false},{armed:true,activate:false,prevent:true}],
  [true,{type:'keydown',key:' ',repeat:true,focused:true,disabled:false},{armed:true,activate:false,prevent:true}],
  [false,{type:'keydown',key:' ',repeat:true,focused:true,disabled:false},{armed:false,activate:false,prevent:true}],
  [true,{type:'keyup',key:' ',focused:true,disabled:false},{armed:false,activate:true,prevent:true}],
  [false,{type:'keyup',key:' ',focused:true,disabled:false},{armed:false,activate:false,prevent:true}],
  [true,{type:'keyup',key:' ',focused:false,disabled:false},{armed:false,activate:false,prevent:true}],
  [true,{type:'blur',focused:false,disabled:false},{armed:false,activate:false,prevent:false}],
  [true,{type:'keyup',key:' ',focused:true,disabled:true},{armed:false,activate:false,prevent:true}],
  [false,{type:'keydown',key:'Enter',focused:true,disabled:true},{armed:false,activate:false,prevent:false}],
  [false,{type:'keydown',key:'a',focused:true,disabled:false},{armed:false,activate:false,prevent:false}]
];
fixtures.forEach(([armed,event,expected])=>assert.deepEqual(keyboard.transition(armed,event),expected));
const scope=JSON.parse(await readFile(path.join(root,'scope.json'),'utf8'));
assert.equal(scope.status,'single-lesson-not-subject-complete'); assert.equal(scope.inventoryExhaustive,false);
assert.equal(new Set(scope.unmade.map(x=>x.id)).size,11);
const browserExpected={
  'native-tab':{focus:'native',nativeCount:0,customCount:0},
  'native-enter':{focus:'native',nativeCount:1,customCount:0},
  'native-space':{focus:'native',nativeCount:2,customCount:0},
  'click-only-tab-skips':{focus:'end',customCount:0,customRoleCount:0},
  'click-only-mouse':{customCount:1,customRoleCount:0},
  'role-only-tab':{focus:'custom',customCount:0,customRoleCount:1,customNamedCount:1},
  'role-only-enter':{focus:'custom',customCount:0},
  'role-only-space':{focus:'custom',customCount:0},
  'repaired-tab':{focus:'custom',customCount:0,customRoleCount:1,customNamedCount:1},
  'repaired-enter':{focus:'custom',customCount:1},
  'repaired-space':{focus:'custom',customCount:2},
  'disabled-tab':{focus:'custom',disabled:true,customCount:2},
  'disabled-enter':{focus:'custom',customCount:2},
  'disabled-space':{focus:'custom',customCount:2},
  'disabled-mouse':{customCount:2},
  'name-missing':{nameCount:0,unnamedEmptyCount:1,unnamedNamedCount:0},
  'name-missing-keyboard':{nameCount:1,focus:'unnamed',unnamedEmptyCount:1},
  'name-restored':{nameCount:1,unnamedEmptyCount:0,unnamedNamedCount:1},
  'quiz-role':{feedbackPrefix:'不足。'},
  'quiz-tab':{feedbackPrefix:'不足。'},
  'quiz-complete':{feedbackPrefix:'条件付きで適切。'},
  'quiz-native':{feedbackPrefix:'適切。'}
};
const args=process.argv.slice(2);
let recordDir=null,browserFile=null;
for(let i=0;i<args.length;i++){
  if(args[i]==='--record'){recordDir=args[++i];if(!/^[a-z][a-z0-9-]+$/.test(recordDir||''))throw new Error('--recordには新しい観測directory名のみ指定');}
  else if(args[i]==='--browser'){browserFile=args[++i];if(!/^observations\/[a-z0-9-]+\/browser.json$/.test(browserFile||''))throw new Error('--browserはmodule内の観測JSONのみ');}
  else throw new Error(`Unknown option ${args[i]}`);
}
let browserChecks=0;
if(browserFile){
  const record=JSON.parse(await readFile(path.join(root,browserFile),'utf8'));
  assert.equal(record.kind,'actual-iab-keyboard-dom-ax');
  assert.ok(record.startedAt&&record.completedAt&&record.environment.userAgent);
  for(const [f,digest] of Object.entries(digests))assert.equal(record.sourceHashes[f],digest,`stale source ${f}`);
  assert.equal(record.observations.length,Object.keys(browserExpected).length);
  for(const [id,expected] of Object.entries(browserExpected)){
    const matches=record.observations.filter(x=>x.id===id); assert.equal(matches.length,1,id);
    const actual=matches[0];assert.ok(actual.at&&actual.input&&actual.snapshot);
    for(const [key,value] of Object.entries(expected)){
      if(key==='feedbackPrefix')assert.ok(actual.feedback.startsWith(value),id);
      else assert.equal(actual[key],value,`${id} ${key}`);
      browserChecks++;
    }
  }
  for(const id of ['native-tab','repaired-tab']){
    const obs=record.observations.find(x=>x.id===id);
    assert.equal(obs.focusVisible,true); assert.notEqual(obs.outlineStyle,'none'); assert.notEqual(obs.outlineWidth,'0px'); browserChecks+=3;
  }
  for(const id of ['native-enter','native-space','repaired-enter','repaired-space','disabled-enter','disabled-space','name-missing-keyboard']){
    const obs=record.observations.find(x=>x.id===id);
    assert.ok(obs.events.some(e=>e.trusted&&(e.type==='keydown'||e.type==='keyup')),id);browserChecks++;
  }
  assert.ok(record.axNameMissing.includes('button'));assert.ok(record.axNameRestored.includes('カウントを増やす'));browserChecks+=2;
}
const report={kind:'node-policy-and-independent-browser-oracle',at:new Date().toISOString(),runtime:{node:process.version,platform:process.platform,arch:process.arch},sourceHashes:digests,unitFixtures:fixtures.map(([armed,event,expected])=>({armed,event,expected,actual:keyboard.transition(armed,event)})),browserFile,browserChecks,passed:true,limitations:['Node policy tests are not native DOM/AT evidence','Stored browser record validation is not a fresh browser run']};
if(recordDir){await mkdir(path.join(root,'observations'),{recursive:true});const dir=path.join(root,'observations',recordDir);await mkdir(dir,{recursive:false});await writeFile(path.join(dir,'node.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});}
console.log(JSON.stringify(report,null,2));
