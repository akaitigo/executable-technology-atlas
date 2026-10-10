// No GPU, workgroup loop, TypedArray or shader translation: exact CPU arithmetic + prefix coverage.
export function oracle(f,c){
  const full=f.a.map((v,i)=>Number((BigInt(v)+BigInt(f.b[i]))%4294967296n));
  if(c.mode!=='compute')return {full,output:null,marks:null,errorName:'GPUValidationError'};
  const lanes=c.groups*f.workgroupSize,covered=Math.min(f.a.length,lanes);
  return {full,output:Array.from({length:f.outputLength},(_,i)=>i<covered?full[i]:f.sentinel),marks:Array.from({length:f.markLength},(_,i)=>i>=lanes?0:i<f.a.length?1:2),errorName:null};
}
export function simulate(f,c){const started=new Date().toISOString();if(c.mode!=='compute')return {kind:'logical-workgroup-simulator-not-gpu',id:c.id,rejected:'validation-case-requires-real-gpu',started,completed:new Date().toISOString()};const output=Array(f.outputLength).fill(f.sentinel),marks=Array(f.markLength).fill(0);for(let group=0;group<c.groups;group++)for(let local=0;local<f.workgroupSize;local++){const id=group*f.workgroupSize+local;if(id>=f.markLength)continue;if(id>=f.a.length){marks[id]=2;continue;}output[id]=(f.a[id]+f.b[id])>>>0;marks[id]=1;}return {kind:'logical-workgroup-simulator-not-gpu',id:c.id,output,marks,started,completed:new Date().toISOString()};}
