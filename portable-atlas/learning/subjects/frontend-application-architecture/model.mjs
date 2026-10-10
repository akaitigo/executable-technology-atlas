export function initialState() {
  const items=[{id:'a',name:'Alpha'},{id:'b',name:'Beta'}];
  return {
    normalized:{ids:['a','b'],byId:Object.fromEntries(items.map(e=>[e.id,{...e}])),selectedId:'a'},
    duplicated:{listItems:structuredClone(items),detailById:Object.fromEntries(items.map(e=>[e.id,{...e}])),selectedId:'a'}
  };
}

export function transition(state,input) {
  const {type,id,name}=input;
  const reject=reason=>({state,outcome:{accepted:false,reason}});
  if(type==='reset')return {state:initialState(),outcome:{accepted:true,reason:'reset'}};
  if(!['select','edit','remove'].includes(type))return reject('unsupported-action');
  if(id===null)return reject('no-selection');
  if(!Object.hasOwn(state.normalized.byId,id))return reject('unknown-entity');
  if(type==='edit'&&(typeof name!=='string'||name.trim().length<1||name.trim().length>24))return reject('invalid-name');
  const next=structuredClone(state);
  if(type==='select') {
    next.normalized.selectedId=id;
    next.duplicated.selectedId=id;
  } else if(type==='edit') {
    const text=name.trim();
    next.normalized.byId[id]={id,name:text};
    // 意図した不十分な更新: detailだけ更新し、保存データのlist copyを更新しない。
    // draftを別stateとして持つ設計一般を否定するものではない。
    next.duplicated.detailById[id]={id,name:text};
  } else {
    next.normalized.ids=next.normalized.ids.filter(key=>key!==id);
    delete next.normalized.byId[id];
    next.duplicated.listItems=next.duplicated.listItems.filter(e=>e.id!==id);
    delete next.duplicated.detailById[id];
    if(next.normalized.selectedId===id)next.normalized.selectedId=null;
    if(next.duplicated.selectedId===id)next.duplicated.selectedId=null;
  }
  return {state:next,outcome:{accepted:true,reason:type}};
}

export function views(state) {
  const n=state.normalized,d=state.duplicated;
  return {
    normalized:{list:n.ids.map(id=>({...n.byId[id]})),detail:n.selectedId?{...n.byId[n.selectedId]}:null,selectedId:n.selectedId,driftIds:[]},
    duplicated:{list:structuredClone(d.listItems),detail:d.selectedId?{...d.detailById[d.selectedId]}:null,selectedId:d.selectedId,driftIds:d.listItems.filter(e=>e.name!==d.detailById[e.id]?.name).map(e=>e.id)}
  };
}
