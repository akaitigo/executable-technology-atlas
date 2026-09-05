import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { sha256 } from './crypto.mjs';

const exactKeys=(value,expected)=>value&&JSON.stringify(Object.keys(value).sort())===JSON.stringify([...expected].sort());

function validateGateResult(gate,graphDigest,lock){
  const errors=[];
  const fields=['schemaVersion','coreCommit','command','result','executedAt','runtimeIdentity','graphDigest','missingRequiredOutputs','structureResults','diagnostics'];
  if(!exactKeys(gate,fields))errors.push('Core Gate resultのfield集合が不正です');
  if(gate?.schemaVersion!==1||gate?.coreCommit!==lock.coreCommit)errors.push('Core Gate resultが固定Core commitへpinされていません');
  if(gate?.command!=='atlas audit . --gate evidence-dependency')errors.push('Core Gate commandがEvidence Dependency Gateではありません');
  if(!['pass','fail'].includes(gate?.result))errors.push('Core Gate resultはpass/failが必要です');
  if(!gate?.executedAt||Number.isNaN(Date.parse(gate.executedAt)))errors.push('Core Gate実行時刻が不正です');
  if(!gate?.runtimeIdentity||typeof gate.runtimeIdentity!=='object'||Array.isArray(gate.runtimeIdentity)||!Object.keys(gate.runtimeIdentity).length)errors.push('Core Gate runtime identityが必要です');
  if(gate?.graphDigest!==graphDigest)errors.push('Core Gate resultのGraph digest bindingが一致しません');
  if(!Array.isArray(gate?.missingRequiredOutputs)||!Array.isArray(gate?.structureResults)||!Array.isArray(gate?.diagnostics))errors.push('Core Gate診断配列が不正です');
  if(gate?.result==='pass'&&((gate.missingRequiredOutputs?.length??0)>0||(gate.structureResults??[]).some((item)=>item.status!=='current')||(gate.diagnostics?.length??0)>0))errors.push('pass Gate resultにmissing outputまたはstructure driftがあります');
  return errors;
}

export function validateEvidenceDependencyEnvelope(envelope,lock,schema,verification){
  const errors=[...(verification?.errors??[])];const payload=envelope?.payload;const graph=payload?.graph;const graphDigest=sha256(graph);
  if(envelope?.kind!=='portal-evidence-dependency')errors.push('Evidence Dependency kindが不正です');
  if(payload?.coreCommit!==lock.coreCommit||payload?.graphPath!=='evidence/dependency-graph.json'||payload?.graphDigest!==graphDigest)errors.push('Graph/Core commit bindingが不正です');
  const ajv=new Ajv2020({allErrors:true,strict:true});addFormats(ajv);let validator=null;try{validator=ajv.compile(schema);}catch(error){errors.push(`Evidence Dependency Schemaをcompileできません: ${error.message}`);}
  if(validator&&!validator(graph))errors.push(`Evidence Dependency Graph Schema不適合: ${ajv.errorsText(validator.errors)}`);
  if(graph?.atlas_id!==payload?.atlasId)errors.push('Graph atlas_idが署名payload bindingと一致しません');
  const inputIds=new Set((graph?.inputs??[]).map((item)=>item.id));const outputIds=new Set((graph?.outputs??[]).map((item)=>item.id));const runIds=new Set((graph?.runs??[]).map((item)=>item.id));
  for(const output of graph?.outputs??[]){if((output.depends_on??[]).some((id)=>!inputIds.has(id)&&!outputIds.has(id)))errors.push(`Output ${output.id}に未知のdependencyがあります`);if(output.run_id&&!runIds.has(output.run_id))errors.push(`Output ${output.id}のrunがありません`);}
  for(const run of graph?.runs??[]){if((run.input_bindings??[]).some((binding)=>!inputIds.has(binding.input_id)))errors.push(`Run ${run.id}に未知のinput bindingがあります`);if((run.output_ids??[]).some((id)=>!outputIds.has(id)))errors.push(`Run ${run.id}に未知のoutputがあります`);}
  const outputPaths=new Set((graph?.outputs??[]).map((item)=>item.path));if((graph?.required_outputs??[]).some((item)=>!outputPaths.has(item)))errors.push('required_outputsにGraph outputがないPathがあります');
  errors.push(...validateGateResult(payload?.coreGate,graphDigest,lock));
  if(payload?.coreGate?.result==='pass'&&(graph?.status!=='current'||(graph?.outputs??[]).some((item)=>item.status!=='current')))errors.push('Core Gate passとGraph current状態が一致しません');
  if(payload?.coreGate?.result==='pass'&&(graph?.runs??[]).some((run)=>['runtime','platform'].includes(run.execution_kind)&&(!run.runtime_identity||!Object.keys(run.runtime_identity).length)))errors.push('Core Gate passのRuntime/Platform runにruntime identityがありません');
  return{ok:errors.length===0,errors,graph,graphDigest,gate:payload?.coreGate??null};
}

function impactIndex(graph){
  const outputsByDependency=new Map();for(const output of graph.outputs??[])for(const dependency of output.depends_on??[]){const list=outputsByDependency.get(dependency)??[];list.push(output.id);outputsByDependency.set(dependency,list);}
  const changed=(graph.inputs??[]).filter((item)=>item.baseline_digest!==item.current_digest).map((item)=>item.id);const impacted=new Map();
  for(const inputId of changed){const queue=[inputId];const seen=new Set();while(queue.length){const dependency=queue.shift();for(const outputId of outputsByDependency.get(dependency)??[])if(!seen.has(outputId)){seen.add(outputId);queue.push(outputId);}}for(const outputId of seen){const list=impacted.get(outputId)??[];list.push(inputId);impacted.set(outputId,list);}}
  return impacted;
}

export function projectEvidenceDependency(envelope,validated,verification){
  const graph=validated.graph;const gate=validated.gate;const runs=new Map((graph.runs??[]).map((item)=>[item.id,item]));const impacted=impactIndex(graph);
  const inputs=(graph.inputs??[]).map((item)=>({...item,state:item.baseline_digest===item.current_digest?'current':'changed'}));
  const outputs=(graph.outputs??[]).map((item)=>{const run=runs.get(item.run_id);return{...item,impacted_by:impacted.get(item.id)??[],run:run?{id:run.id,command:run.command,result:run.result,attempts:run.attempts,started_at:run.started_at,completed_at:run.completed_at,execution_kind:run.execution_kind,runtime_identity:run.runtime_identity??null,input_bindings:run.input_bindings}:null};});
  return{schemaVersion:1,subjectId:envelope.payload.subjectId,atlasId:envelope.payload.atlasId,availability:'available',status:gate.result==='pass'?'current':'stale-or-incomplete',graphStatus:graph.status,generatedAt:graph.generated_at,policy:graph.policy,summary:{inputs:inputs.length,inputChanged:inputs.filter((item)=>item.state==='changed').length,inputCurrent:inputs.filter((item)=>item.state==='current').length,outputs:outputs.length,outputStale:outputs.filter((item)=>item.status==='stale').length,outputCurrent:outputs.filter((item)=>item.status==='current').length,impactedOutputs:outputs.filter((item)=>item.impacted_by.length).length,runs:graph.runs.length,missingRequiredOutputs:gate.missingRequiredOutputs.length,structureDrift:gate.structureResults.filter((item)=>item.status!=='current').length},inputs,outputs,requiredOutputs:graph.required_outputs,structures:graph.structures.map((item)=>({...item,gate:gate.structureResults.find((result)=>result.id===item.id)??{id:item.id,status:'missing',detail:'Core Gate structure result missing'}})),coreGate:gate,source:{repository:envelope.payload.repository,commit:envelope.payload.sourceCommit,graphPath:envelope.payload.graphPath,graphDigest:validated.graphDigest,envelopeDigest:envelope.release.digest,trust:verification.trust},readOnly:true,autoPromotion:false};
}

export function missingEvidenceDependency(subject){
  return{schemaVersion:1,subjectId:subject.id,atlasId:null,availability:'missing',status:'missing-required-output',graphStatus:null,summary:{inputs:0,inputChanged:0,inputCurrent:0,outputs:0,outputStale:0,outputCurrent:0,impactedOutputs:0,runs:0,missingRequiredOutputs:1,structureDrift:2},coreGate:{result:'not-run',command:'atlas audit . --gate evidence-dependency',coreCommit:null,runtimeIdentity:null,diagnostics:['evidence/dependency-graph.jsonが固定Releaseにありません']},missingRequiredOutputs:['evidence/dependency-graph.json'],structures:[{id:'scenario-proof-index',status:'not-evaluated'},{id:'scenario-closure-plan',status:'not-evaluated'}],detailUrl:null,readOnly:true,autoPromotion:false};
}
