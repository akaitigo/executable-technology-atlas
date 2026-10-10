const events=[];
const counts={};
export function record(type,detail={}){const event={sequence:events.length+1,at:new Date().toISOString(),elapsedMs:performance.now(),type,detail};events.push(event);return event;}
export function evaluated(module){counts[module]=(counts[module]||0)+1;record('module-evaluated',{module,ordinal:counts[module]});return counts[module];}
export function journal(){return {events:structuredClone(events),evaluationCounts:{...counts}};}
evaluated('journal');
