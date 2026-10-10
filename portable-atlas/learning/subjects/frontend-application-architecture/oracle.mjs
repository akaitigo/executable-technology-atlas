// model/selector/DOMをimportせず、固定した入力と保存/表示stateの期待値を記述する。
const LONG='abcdefghijklmnopqrstuvwx';
function expected(normalNames,detailNames,selectedId,reason,accepted=true) {
  const ids=normalNames.map(x=>x[0]);
  const normal=Object.fromEntries(normalNames.map(([id,name])=>[id,{id,name}]));
  const details=Object.fromEntries(detailNames.map(([id,name])=>[id,{id,name}]));
  const list=ids.map(id=>({id,name:id==='a'?'Alpha':'Beta'}));
  return {
    state:{normalized:{ids,byId:normal,selectedId},duplicated:{listItems:list,detailById:details,selectedId}},
    views:{normalized:{list:normalNames.map(([id,name])=>({id,name})),detail:selectedId?normal[selectedId]:null,selectedId,driftIds:[]},duplicated:{list,detail:selectedId?details[selectedId]:null,selectedId,driftIds:ids.filter(id=>details[id].name!==(id==='a'?'Alpha':'Beta'))}},
    outcome:{accepted,reason}
  };
}
const initial=[['a','Alpha'],['b','Beta']],orbit=[['a','Orbit'],['b','Beta']],long=[['a',LONG],['b','Beta']],signal=[['a',LONG],['b','Signal']];
export const STEPS=[
 {id:'initial',input:null,...expected(initial,initial,'a','initial')},
 {id:'edit-a',input:{type:'edit',id:'a',name:'Orbit'},...expected(orbit,orbit,'a','edit')},
 {id:'invalid-empty',input:{type:'edit',id:'a',name:'   '},...expected(orbit,orbit,'a','invalid-name',false)},
 {id:'boundary24-a',input:{type:'edit',id:'a',name:LONG},...expected(long,long,'a','edit')},
 {id:'invalid25',input:{type:'edit',id:'a',name:LONG+'y'},...expected(long,long,'a','invalid-name',false)},
 {id:'select-b',input:{type:'select',id:'b'},...expected(long,long,'b','select')},
 {id:'edit-b',input:{type:'edit',id:'b',name:'Signal'},...expected(signal,signal,'b','edit')},
 {id:'unknown-select',input:{type:'select',id:'ghost'},...expected(signal,signal,'b','unknown-entity',false)},
 {id:'unknown-edit',input:{type:'edit',id:'ghost',name:'Ghost'},...expected(signal,signal,'b','unknown-entity',false)},
 {id:'unknown-remove',input:{type:'remove',id:'ghost'},...expected(signal,signal,'b','unknown-entity',false)},
 {id:'remove-b',input:{type:'remove',id:'b'},...expected([['a',LONG]],[['a',LONG]],null,'remove')},
 {id:'remove-no-selection',input:{type:'remove',id:null},...expected([['a',LONG]],[['a',LONG]],null,'no-selection',false)},
 {id:'select-a',input:{type:'select',id:'a'},...expected([['a',LONG]],[['a',LONG]],'a','select')},
 {id:'remove-a',input:{type:'remove',id:'a'},...expected([],[],null,'remove')},
 {id:'select-deleted-a',input:{type:'select',id:'a'},...expected([],[],null,'unknown-entity',false)},
 {id:'edit-no-selection',input:{type:'edit',id:null,name:'Orbit'},...expected([],[],null,'no-selection',false)},
 {id:'reset',input:{type:'reset'},...expected(initial,initial,'a','reset')}
];
