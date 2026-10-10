// SPDX-License-Identifier: Apache-2.0
const section=(id,payload)=>[id,payload.length,...payload];
const name=s=>[s.length,...new TextEncoder().encode(s)];
export function moduleBytes(){return Uint8Array.from([
 0,97,115,109,1,0,0,0,
 ...section(1,[1,96,1,127,1,127]),
 ...section(3,[2,0,0]),
 ...section(5,[1,1,1,2]),
 ...section(7,[3,...name('memory'),2,0,...name('load8'),0,0,...name('grow'),0,1]),
 ...section(10,[2,7,0,32,0,45,0,0,11,6,0,32,0,64,0,11])
]);}
