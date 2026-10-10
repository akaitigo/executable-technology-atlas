// Explicit Euler: position first, velocity second. A point overlaps a finite floor band only at step end.
export function simulate(input) {
  const started=new Date().toISOString();
  const valid=input.framesMs.length===2&&input.paused.length===2&&input.framesMs.every(x=>Number.isSafeInteger(x)&&x>=0&&x<=10000)&&input.paused.every(x=>typeof x==='boolean')&&Number.isSafeInteger(input.stepMs)&&input.stepMs>0&&Number.isSafeInteger(input.capMs)&&input.capMs>0&&input.capMs<=1000&&[input.y0,input.v0,input.gravity].every(Number.isFinite)&&(input.floor===null||(input.floor.length===2&&input.floor.every(Number.isFinite)&&input.floor[0]<input.floor[1]));
  if(!valid)return {id:input.id,input,started,completed:new Date().toISOString(),stage:'rejected',error:{name:'RangeError',message:'frame入力を状態変更前に拒否'},frames:[],steps:[],final:null};
  const states={variable:{y:input.y0,v:input.v0,grounded:false},fixed:{y:input.y0,v:input.v0,grounded:false}};
  const ticks={variable:0,fixed:0},steps=[],frames=[];let accumulatorMs=0,acceptedMs=0,discardedMs=0;
  function advance(algorithm,deltaMs,frame){const before={...states[algorithm]},s=states[algorithm];let endpointY=s.y,collision=false,crossedBand=false;
    if(!s.grounded){endpointY=s.y+s.v*deltaMs/1000;s.y=endpointY;s.v+=input.gravity*deltaMs/1000;if(input.floor){crossedBand=before.y<input.floor[0]&&endpointY>input.floor[1];collision=endpointY>=input.floor[0]&&endpointY<=input.floor[1];if(collision){s.y=input.floor[0];s.v=0;s.grounded=true;}}}
    steps.push({algorithm,tick:++ticks[algorithm],frame,deltaMs,before,endpointY,collision,crossedBand,after:{...s}});
  }
  for(let i=0;i<input.framesMs.length;i++){const rawDeltaMs=input.framesMs[i],paused=input.paused[i],deltaMs=paused?0:Math.min(rawDeltaMs,input.capMs);acceptedMs+=deltaMs;discardedMs+=rawDeltaMs-deltaMs;if(deltaMs>0)advance('variable',deltaMs,i);accumulatorMs+=deltaMs;let substeps=0;while(accumulatorMs>=input.stepMs){advance('fixed',input.stepMs,i);accumulatorMs-=input.stepMs;substeps++;}
    frames.push({frame:i,rawDeltaMs,paused,acceptedDeltaMs:deltaMs,discardedDeltaMs:rawDeltaMs-deltaMs,acceptedMs,discardedMs,accumulatorMs,substeps,variable:{...states.variable},fixed:{...states.fixed}});
  }
  return {id:input.id,input,started,completed:new Date().toISOString(),stage:'simulated',error:null,frames,steps,final:{...states,acceptedMs,discardedMs,accumulatorMs,variableTicks:ticks.variable,fixedTicks:ticks.fixed,variableSimulatedMs:acceptedMs,fixedSimulatedMs:ticks.fixed*input.stepMs}};
}
