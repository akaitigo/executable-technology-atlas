// Runnerをimportせず、HTML checkpointとPromise reactionの規則から固定した期待値。
export const EXPECTED=Object.freeze({
 basic:['sync-start','sync-end','micro-parent','timer-first','timer-micro','timer-second'],
 nested:['sync-start','sync-end','micro-parent','micro-peer','micro-child','micro-grandchild','timer-first','timer-micro','timer-second'],
 'caught-error':['sync-start','sync-end','micro-throw','micro-peer','micro-caught','timer-first','timer-micro','timer-second']
});
export function compare(caseId,trace){
 const expected=EXPECTED[caseId];if(!expected)throw new RangeError('unsupported case');
 const actual=trace.map(e=>e.label);const wrong=[...expected];
 // 誤モデル: 初回checkpointで追加されたmicrotaskは次timerへ先送り、と仮定する。
 if(caseId==='nested'){wrong.splice(4,2);wrong.splice(5,0,'micro-child','micro-grandchild');}
 else{const micro=wrong.splice(2,caseId==='basic'?1:3);wrong.splice(3,0,...micro);}
 return {expected:[...expected],actual,passed:JSON.stringify(expected)===JSON.stringify(actual),wrongModel:wrong,wrongModelMatches:JSON.stringify(wrong)===JSON.stringify(actual),firstWrongIndex:wrong.findIndex((v,i)=>v!==actual[i])};
}
