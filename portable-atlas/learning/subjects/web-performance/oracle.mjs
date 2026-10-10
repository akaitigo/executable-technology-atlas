// 実験/plan/CSSをimportせず、固定fixtureの幾何と操作回数を期待する。時間の勝敗は期待しない。
export const NORMAL_WIDTHS=[100,108,116,124,100,108,116,124,100,108,116,124,100,108,116,124];
export const ZERO_WIDTHS=Array(16).fill(80);
export function expectedGeometry(iterations){const w=iterations===8?NORMAL_WIDTHS:ZERO_WIDTHS;return w.map((width,id)=>({id,width,height:32,x:9+(id%4)*148,y:9+Math.floor(id/4)*40,computedWidth:width+'px'}));}
export const EXPECTED={cells:16,iterations:[8,0],warmup:2,measured:5,reads:128,writes:128,checksum:14080,timerCases:[{id:'idle',delayMs:20,blockMs:0},{id:'long-timer',delayMs:100,blockMs:0},{id:'blocking',delayMs:20,blockMs:120}],timerToleranceMs:2};
export const EXPECTED_ORDERS=[['interleaved','batched'],['batched','interleaved'],['interleaved','batched'],['batched','interleaved'],['interleaved','batched'],['batched','interleaved'],['interleaved','batched']];
