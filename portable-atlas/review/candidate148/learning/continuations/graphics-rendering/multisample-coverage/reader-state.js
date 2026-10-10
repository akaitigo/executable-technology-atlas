(function(root){
  'use strict';
  const scenes=['edge-low','edge-high','overlap-ab','overlap-ba','shared-edge'];
  const modes=['normal','missing','altered','old'];
  function canonical(v){
    if(Array.isArray(v))return '['+v.map(canonical).join(',')+']';
    if(v!==null&&typeof v==='object')return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';
    return JSON.stringify(v);
  }
  function initial(){return {scene:'edge-low',pixel:1,centerPrediction:'',fourPrediction:'',mode:'normal',step:0,shown:null,answer:false,error:''};}
  function clear(s){return {...s,step:0,shown:null,answer:false,error:''};}
  function valid(data,expected){
    return !!data&&!!expected&&data.schema===1&&canonical(data)===canonical(expected)&&
      typeof data.run_id==='string'&&typeof data.observed_at_utc==='string'&&typeof data.result_sha256==='string';
  }
  function transition(s,e,data,expected){
    if(e.type==='reset')return initial();
    if(e.type==='scene'&&scenes.includes(e.value))return {...clear(s),scene:e.value,centerPrediction:'',fourPrediction:''};
    if(e.type==='pixel'&&Number.isInteger(e.value)&&e.value>=0&&e.value<4)return {...clear(s),pixel:e.value,centerPrediction:'',fourPrediction:''};
    if(e.type==='prediction'&&((e.key==='centerPrediction'&&['0','1'].includes(e.value))||(e.key==='fourPrediction'&&['0','1','2','3','4'].includes(e.value))))return {...clear(s),[e.key]:e.value};
    if(e.type==='mode'&&modes.includes(e.value))return {...clear(s),mode:e.value};
    if(e.type==='load'){
      const n=clear(s);
      if(s.centerPrediction===''||s.fourPrediction==='')return {...n,error:'両配置でAが残る点数を予想してください。'};
      if(!valid(data,expected))return {...n,error:'保存記録が欠落しているか、固定した内容・由来と一致しません。'};
      const pair=['center','four'].map(layout=>data.result.results.find(r=>r.scene_id===s.scene&&r.layout_id===layout));
      if(pair.some(r=>!r))return {...n,error:'選んだ条件の保存記録がありません。'};
      return {...n,shown:pair};
    }
    if(e.type==='step'&&s.shown&&Number.isInteger(e.value)&&e.value>=0&&e.value<s.shown[0].pixels[s.pixel].stages.length)return {...s,step:e.value,answer:false,error:''};
    if(e.type==='answer'&&s.shown)return {...s,answer:true};
    return s;
  }
  function snapshots(s){return s.shown?s.shown.map(r=>r.pixels[s.pixel].stages[s.step]):null;}
  root.ATLAS_STATE={scenes,modes,canonical,initial,clear,valid,transition,snapshots};
  if(typeof module!=='undefined')module.exports=root.ATLAS_STATE;
})(globalThis);
