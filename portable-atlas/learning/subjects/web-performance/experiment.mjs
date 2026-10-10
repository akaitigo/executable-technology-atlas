import {CONFIG,widthFor,orderFor,validateIterations} from './plan.mjs';
const grid=document.getElementById('grid');
export const cells=[...grid.children];
export function geometry(){const origin=grid.getBoundingClientRect();return cells.map((e,i)=>{const r=e.getBoundingClientRect();return {id:i,width:r.width,height:r.height,x:r.x-origin.x,y:r.y-origin.y,computedWidth:getComputedStyle(e).width};});}
function reset(){for(const e of cells)e.style.width='80px';grid.getBoundingClientRect();}
function sample(mode,iterations,phase,round){reset();let checksum=0;const startedAt=new Date().toISOString(),start=performance.now();
 for(let iteration=0;iteration<iterations;iteration++){
  if(mode==='interleaved'){for(let i=0;i<cells.length;i++){cells[i].style.width=widthFor(i,iteration)+'px';checksum+=cells[i].getBoundingClientRect().width;}}
  else {for(let i=0;i<cells.length;i++)cells[i].style.width=widthFor(i,iteration)+'px';for(const e of cells)checksum+=e.getBoundingClientRect().width;}
 }
 const end=performance.now();return {mode,phase,round,startedAt,completedAt:new Date().toISOString(),start,end,elapsedMs:end-start,iterations,reads:iterations*16,writes:iterations*16,checksum,geometry:geometry()};
}
export function runPair(iterations){if(!validateIterations(iterations))return {accepted:false,reason:'unsupported-iterations',iterations,geometry:geometry()};const samples=[];
 for(let r=0;r<CONFIG.warmupRounds+CONFIG.measuredRounds;r++){const phase=r<CONFIG.warmupRounds?'warmup':'measured',round=phase==='warmup'?r:r-CONFIG.warmupRounds;for(const mode of orderFor(r))samples.push(sample(mode,iterations,phase,round));}
 return {accepted:true,iterations,config:CONFIG,samples};
}
export async function runResponsiveness(){const cases=[];for(const c of CONFIG.timerCases){const events=[],start=performance.now(),startedAt=new Date().toISOString(),mark=(name,extra={})=>events.push({name,t:performance.now(),at:new Date().toISOString(),...extra});mark('timer-scheduled',{requestedDelayMs:c.delayMs});
 const completion=new Promise(resolve=>setTimeout(()=>{mark('timer-fired');resolve();},c.delayMs));queueMicrotask(()=>mark('microtask'));
 mark('work-start');const blockStart=performance.now();let spins=0;while(performance.now()-blockStart<c.blockMs)spins++;const blockEnd=performance.now();mark('work-end',{spins});mark('handler-return');await completion;
 const fired=events.find(e=>e.name==='timer-fired');cases.push({...c,startedAt,completedAt:new Date().toISOString(),start,blockStart,blockEnd,actualBlockMs:blockEnd-blockStart,firedAt:fired.t,actualTimerMs:fired.t-start,events});}
 return {kind:'actual-timer-main-thread-probe-not-inp',config:CONFIG.timerCases,cases};
}
export function clockProbe(){const deltas=[];let last=performance.now();for(let i=0;i<128;i++){const n=performance.now();if(n>last)deltas.push(n-last);last=n;}return {attempts:128,minimumObservedPositiveDeltaMs:deltas.length?Math.min(...deltas):null,explanation:'Observed positive delta is not guaranteed clock resolution or statistical uncertainty. Zero-duration samples and scheduling noise are retained.'};}
