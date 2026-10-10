import {readFileSync} from 'node:fs';
export const vectors=JSON.parse(readFileSync(new URL('vectors.json',import.meta.url)));
const scalars=JSON.parse(readFileSync(new URL('oracle.json',import.meta.url))).scalars;
// Independent numeric range arithmetic, not String iterator/TextEncoder/validator.
export function expected(id,runtime){const p=scalars[id];if(p===undefined)throw Error('unknown vector');if(p===null)return {error:id==='not-string'?'not-string':'unpaired-surrogate',codePoints:null,utf16Units:null,utf8Bytes:null,legacyAccepted:false,codePointAccepted:false,byteAccepted:false};const cp=p.length,u=p.reduce((n,v)=>n+(v>65535?2:1),0),b=p.reduce((n,v)=>n+(v<128?1:v<2048?2:v<65536?3:4),0);return {error:null,codePoints:cp,utf16Units:u,utf8Bytes:b,legacyAccepted:(runtime==='python'?cp:u)>=1&&(runtime==='python'?cp:u)<=4,codePointAccepted:cp>=1&&cp<=4,byteAccepted:b>=1&&b<=8};}
