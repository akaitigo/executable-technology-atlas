(function(root){'use strict';const data=typeof module!=='undefined'&&module.exports?require('./reader-data.js'):root.DeadlineData;
 const validate=order=>{if(!data.orders.includes(order))throw new Error('固定6順序から選んでください');return order;};
 function initial(order='CBA'){return{order:validate(order),average:null,deadline:null,tick:0,compared:false,answer:false,error:null};}
 function predict(s,key,value){if(!['average','deadline'].includes(key)||!(key==='average'?['lower','equal','higher']:['all','some']).includes(value))throw new Error('予想が範囲外です');return{...s,[key]:value,tick:0,compared:false,answer:false,error:null};}
 function compare(s){if(s.average===null||s.deadline===null)return{...s,tick:0,compared:false,answer:false,error:'平均待ちと期限達成の両方を予想してください。'};return{...s,compared:true,answer:false,error:null};}
 function tick(s,value){if(!s.compared)throw new Error('予想して比較を表示してください');if(!Number.isInteger(value)||value<0||value>7)throw new Error('時刻は0から7の整数です');return{...s,tick:value};}
 function reveal(s){if(!s.compared)throw new Error('比較を表示してください');return{...s,answer:true};}
 function view(s){const selected=data.outcomes[s.order],fifo=data.outcomes.ABC;return{selected,fifo,frame:s.compared?data.frames.find(f=>f.order===s.order&&f.tick===s.tick).jobs:null,fifoFrame:s.compared?data.frames.find(f=>f.order==='ABC'&&f.tick===s.tick).jobs:null,score:s.answer?{average:s.average===(selected.sum_wait<fifo.sum_wait?'lower':selected.sum_wait===fifo.sum_wait?'equal':'higher'),deadline:s.deadline===(selected.missed.length?'some':'all')}:null};}
 const api={data,validate,initial,predict,compare,tick,reveal,view};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.DeadlineReader=api;
})(globalThis);
