const gcd=(a,b)=>b?gcd(b,a%b):a;
const q=(n,d=1n)=>{n=BigInt(n);d=BigInt(d);const g=gcd(n<0n?-n:n,d);return [n/g,d/g]};
const add=(a,b)=>q(a[0]*b[1]+b[0]*a[1],a[1]*b[1]);
const sub=(a,b)=>q(a[0]*b[1]-b[0]*a[1],a[1]*b[1]);
const mul=(a,b)=>q(a[0]*b[0],a[1]*b[1]);
const str=a=>a[1]===1n?String(a[0]):`${a[0]}/${a[1]}`;
export function simulate(input){
 const valid=input&&typeof input==='object'&&!Array.isArray(input)&&Object.keys(input).sort().join(',')==='framesMs,mode'&&Array.isArray(input.framesMs)&&input.framesMs.length>=1&&input.framesMs.length<=8&&input.framesMs.every(x=>Number.isSafeInteger(x)&&x>=0&&x<=100)&&['NORMAL','FAULT_WRITEBACK'].includes(input.mode);
 if(!valid)return {status:'REFUSED',reason:'INPUT_SCHEMA',input,trace:[],ticks:[]};
 let previous=q(0),current=q(0),remainder=0,totalTicks=0,syntheticMs=0;const trace=[],ticks=[];
 for(const [frame,delta] of input.framesMs.entries()){
  syntheticMs+=delta;remainder+=delta;const stateBefore=str(current);
  while(remainder>=20){previous=current;current=add(current,q(20));remainder-=20;totalTicks++;ticks.push({frame,tick:totalTicks,previous:str(previous),current:str(current),stepMs:20});}
  const alpha=q(remainder,20),render=add(previous,mul(sub(current,previous),alpha));
  const stateBeforeRender=str(current);
  if(input.mode==='FAULT_WRITEBACK')current=render;
  trace.push({frame,deltaMs:delta,syntheticMs,stateBefore,previous:str(previous),current:stateBeforeRender,remainderMs:remainder,alpha:str(alpha),render:str(render),stateAfterRender:str(current),totalTicks});
 }
 return {status:'OK',input,trace,ticks};
}
