// Independent closed form; does not import the runtime recurrence. All clocks are integer milliseconds.
export function expected(c){
  if(c.framesMs.some(x=>!Number.isSafeInteger(x)||x<0||x>10000))return {stage:'rejected',errorName:'RangeError',frames:[],steps:[],final:null};
  const accepted=c.framesMs.map((x,i)=>c.paused[i]?0:Math.min(x,c.capMs)),steps=[],frames=[];
  const free=(deltas)=>{const T=deltas.reduce((a,b)=>a+b,0)/1000,Q=deltas.reduce((a,b)=>a+b*b,0)/1e6;return {y:c.y0+c.v0*T+c.gravity*(T*T-Q)/2,v:c.v0+c.gravity*T,grounded:false};};
  const state=(deltas)=>{if(c.floor){for(let k=1;k<=deltas.length;k++){const y=free(deltas.slice(0,k)).y;if(y>=c.floor[0]&&y<=c.floor[1])return {y:c.floor[0],v:0,grounded:true};}}return free(deltas);};
  const histories={variable:[],fixed:[]};let prefix=0,dropped=0;
  function analyticStep(a,dt,i){const history=histories[a],before=state(history);history.push(dt);const candidate=free(history),endpointY=before.grounded?before.y:candidate.y,collision=!before.grounded&&c.floor!==null&&endpointY>=c.floor[0]&&endpointY<=c.floor[1],crossedBand=!before.grounded&&c.floor!==null&&before.y<c.floor[0]&&endpointY>c.floor[1];steps.push({algorithm:a,tick:history.length,frame:i,deltaMs:dt,before,endpointY,collision,crossedBand,after:state(history)});}
  accepted.forEach((dt,i)=>{const oldTicks=Math.floor(prefix/c.stepMs);prefix+=dt;dropped+=c.framesMs[i]-dt;if(dt>0)analyticStep('variable',dt,i);const n=Math.floor(prefix/c.stepMs);for(let k=oldTicks;k<n;k++)analyticStep('fixed',c.stepMs,i);frames.push({frame:i,rawDeltaMs:c.framesMs[i],paused:c.paused[i],acceptedDeltaMs:dt,discardedDeltaMs:c.framesMs[i]-dt,acceptedMs:prefix,discardedMs:dropped,accumulatorMs:prefix%c.stepMs,substeps:n-oldTicks,variable:state(histories.variable),fixed:state(histories.fixed)});});
  return {stage:'simulated',errorName:null,frames,steps,final:{variable:state(histories.variable),fixed:state(histories.fixed),acceptedMs:prefix,discardedMs:dropped,accumulatorMs:prefix%c.stepMs,variableTicks:histories.variable.length,fixedTicks:histories.fixed.length,variableSimulatedMs:prefix,fixedSimulatedMs:histories.fixed.length*c.stepMs}};
}
export function ballistic(c,acceptedMs){const t=acceptedMs/1000;return c.y0+c.v0*t+c.gravity*t*t/2;}
