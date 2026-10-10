/* Atlas: pure state checks only. No DOM, browser, SQL or Mac runtime. */
function checkAtlasDimensionReader(S,D){
 const checks=[],ok=(v,label)=>{if(!v)throw Error(label);checks.push(label);},step=(s,a,d=D)=>S.transition(s,a,d),clone=x=>JSON.parse(JSON.stringify(x));
 S.IDS.forEach((id,k)=>{
  let s=step(S.initial(),{type:'policy',value:id});s=step(s,{type:'load'});ok(s.shown===null&&s.error.length>0,'prediction required '+id);
  s=step(s,{type:'prediction',value:['undefined','1/4','1/5'][k]});s=step(s,{type:'load'});ok(s.shown?.policy===id&&!s.answer&&!s.error,'load '+id);
  s=step(s,{type:'answer'});ok(s.answer===true,'answer '+id);
  for(const action of [{type:'prediction',value:'1/5'},{type:'policy',value:S.IDS[(k+1)%3]},{type:'record',value:'missing'},{type:'reset'}]){
   const z=step(s,action);ok(z.shown===null&&!z.answer&&!z.error,'clear '+id+' '+action.type);
  }
  for(const mode of ['missing','altered','old']){
   let z=step(s,{type:'record',value:mode});z=step(z,{type:'load'});ok(z.shown===null&&!z.answer&&z.error.length>0,'record refusal '+id+' '+mode);
   z=step(z,{type:'record',value:'normal'});z=step(z,{type:'load'});ok(z.shown?.policy===id&&!z.answer&&!z.error,'recovery '+id+' '+mode);
  }
  for(const n of [0,1]){const z=step(s,{type:'fk',value:n});ok(z.fk===n&&z.shown?.policy===id,'independent FK selection '+id+' '+n);}
 });
 let loaded=step(S.initial(),{type:'prediction',value:'1/5'});loaded=step(loaded,{type:'load'});loaded=step(loaded,{type:'answer'});
 const bad=[['order_amount',x=>x.fixture.orders[2][2]=999],['null_key',x=>x.fixture.orders[3][1]=999],['line_id',x=>x.fixture.lines[0][1]=5],['customer',x=>x.fixture.customers[0][0]=999],['null_rule',x=>x.fixture.null_customer_policy='reject'],['extra_fixture_key',x=>x.fixture.extra=1],['fixture_missing',x=>delete x.fixture],['empty_data',x=>x.policies=[]],['bad_metric',x=>x.policies[2].sum_amount=999],['bad_fk_ids',x=>x.foreign_key_probes[1].events[2].saved_ids.push(3)],['fk_null_error',x=>x.foreign_key_probes[1].events[3].outcome='foreign_key_constraint'],['missing_probe',x=>x.foreign_key_probes.pop()]];
 for(const [name,edit] of bad){const d=clone(D);edit(d);const z=step(loaded,{type:'load'},d);ok(z.shown===null&&!z.answer&&!!z.error,'modified/missing refusal '+name);}
 ok(step(loaded,{type:'load'},null).shown===null,'missing dataset');
 ok(step(loaded,{type:'policy',value:'unknown'}).shown===null,'unknown policy clears');
 const no=step(step(S.initial(),{type:'policy',value:'reject-batch'}),{type:'prediction',value:'1/5'});const wrong=step(step(no,{type:'load'}),{type:'answer'});ok(wrong.answer&&wrong.shown.missing_fraction===null&&wrong.prediction==='1/5','wrong prediction remains separate');
 return {title:'Atlas dimension-policy pure state checks',passed:true,checks,policies:3,dom_observed:false,browser_started:false,sqlite_reexecuted:false};
}
