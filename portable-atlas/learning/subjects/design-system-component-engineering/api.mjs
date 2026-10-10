export const IDS=['bug-a','bug-b','safe-a','safe-b'];
export const initial=()=>({theme:'light',override:'',disabled:false,counts:Object.fromEntries(IDS.map(id=>[id,0]))});
// このAPIでは移植しやすい6桁hexだけをinstance色として受け付ける。
export const validOverride=v=>typeof v==='string'&&/^#[0-9a-f]{6}$/i.test(v);
export function apply(state,input){
 const reject=reason=>({state,outcome:{accepted:false,reason}});
 if(input.type==='reset')return {state:initial(),outcome:{accepted:true,reason:'reset'}};
 const next=structuredClone(state);
 if(input.type==='theme'){if(!['light','dark'].includes(input.value))return reject('unsupported-theme');next.theme=input.value;}
 else if(input.type==='override'){if(typeof input.value!=='string'||input.value.length>64)return reject('invalid-input');next.override=input.value;}
 else if(input.type==='disabled'){if(typeof input.value!=='boolean')return reject('invalid-input');next.disabled=input.value;}
 else if(input.type==='activate'){if(!IDS.includes(input.id))return reject('unknown-instance');if(state.disabled&&input.id.endsWith('-a'))return reject('disabled');next.counts[input.id]++;}
 else return reject('unsupported-action');
 return {state:next,outcome:{accepted:true,reason:input.type==='override'&&input.value&&!validOverride(input.value)?'safe-fallback-bug-raw':'applied'}};
}
