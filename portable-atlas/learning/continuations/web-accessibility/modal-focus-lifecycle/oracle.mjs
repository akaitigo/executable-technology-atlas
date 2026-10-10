// APG-derived desired checkpoints are independent of DOM/event handlers. No runtime import.
const columns={
 'native-basic':[['launch',false],['native-first',true],['native-close',true],['native-first',true],['launch',false]],
 'native-wrap':[['launch',false],['native-first',true],['native-close',true],['native-first',true],['native-close',true],['launch',false]],
 'native-close':[['launch',false],['native-first',true],['native-close',true],['launch',false]],
 'role-fault':[['launch',false],['role-first',true],['role-close',true],['role-first',true],['role-close',true],['launch',false],null,null,['launch',false]]
};
export function expectedAt(id,index){const value=columns[id]?.[index];if(value===undefined)throw Error('unknown checkpoint');return value?{activeId:value[0],surfaceOpen:value[1]}:null;}
export function compare(id,index,state){const expected=expectedAt(id,index);if(expected===null)return {expected:null,compared:false,focusMatches:null,openMatches:null,matches:null,note:'故障版を閉じるためのcleanup移動。APG循環の比較対象ではない。'};const focusMatches=state.active.id===expected.activeId,openMatches=state.surfaceOpen===expected.surfaceOpen;return {expected,compared:true,focusMatches,openMatches,matches:focusMatches&&openMatches,note:focusMatches&&openMatches?'期待と一致':'実測差異を保持。期待値へ補正しない。'};}
