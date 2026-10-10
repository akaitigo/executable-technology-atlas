// CSS/API/selectorをimportしない独立した固定期待表。rgba透明も意図異常の期待であり改善ではない。
export const TOKENS={light:{background:'rgb(29, 78, 216)',color:'rgb(255, 255, 255)'},dark:{background:'rgb(147, 197, 253)',color:'rgb(16, 36, 60)'},override:{background:'rgb(157, 23, 77)',color:'rgb(255, 255, 255)'},invalid:{background:'rgba(0, 0, 0, 0)',color:'rgb(255, 255, 255)'}};
const ids=['bug-a','bug-b','safe-a','safe-b'];
function fixed(id,input,theme,override,disabled,count=0,active=null){const state={theme,override,disabled,counts:{'bug-a':0,'bug-b':0,'safe-a':count,'safe-b':0}};const metrics=Object.fromEntries(ids.map(b=>{const t=override==='not-a-color'&&b.startsWith('bug')?TOKENS.invalid:override==='#9d174d'&&(b.startsWith('bug')||b==='safe-a')?TOKENS.override:TOKENS[theme];const off=disabled&&b.endsWith('-a');return [b,{...t,radius:'8px',minHeight:'40px',padding:'8px 16px',opacity:off?'0.45':'1',disabled:off,disabledAttribute:off,type:'button',variant:'primary',text:({'bug-a':'漏れ版 A','bug-b':'漏れ版 B','safe-a':'局所版 A','safe-b':'局所版 B'})[b],instanceToken:b.startsWith('bug')?override:b==='safe-a'&&override==='#9d174d'?override:'',count:state.counts[b]}];}));return {id,input,state,metrics,active};}
export const STEPS=[
 fixed('initial',null,'light','',false),
 fixed('dark',{type:'theme',value:'dark'},'dark','',false),
 fixed('light',{type:'theme',value:'light'},'light','',false),
 fixed('leak',{type:'override',value:'#9d174d'},'light','#9d174d',false),
 fixed('invalid',{type:'override',value:'not-a-color'},'light','not-a-color',false),
 fixed('clear',{type:'override',value:''},'light','',false),
 fixed('disabled',{type:'disabled',value:true},'light','',true),
 fixed('tab-skip-bug-a',null,'light','',true,0,'bug-b'),
 fixed('tab-skip-safe-a',null,'light','',true,0,'safe-b'),
 fixed('enabled',{type:'disabled',value:false},'light','',false),
 fixed('enter',{type:'activate',id:'safe-a'},'light','',false,1,'safe-a'),
 fixed('space',{type:'activate',id:'safe-a'},'light','',false,2,'safe-a'),
 fixed('reset',{type:'reset'},'light','',false)
];
