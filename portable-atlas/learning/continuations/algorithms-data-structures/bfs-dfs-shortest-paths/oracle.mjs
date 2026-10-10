// search.mjsをimportしない。単純pathの全列挙（pathごとの訪問禁止）から距離を求める。
export function contract(input){
  if(!input||!input.graph||typeof input.graph!=='object'||Array.isArray(input.graph))return 'graph-object';
  const names=Object.keys(input.graph);if(names.length===0||names.length>8||names.some(n=>!n.match(/^[A-Z][A-Z0-9]{0,2}$/)))return 'vertices';
  if(!names.some(n=>n===input.start)||!names.some(n=>n===input.target))return 'endpoint';
  let n=0;for(const list of Object.values(input.graph)){if(!Array.isArray(list))return 'adjacency';for(let i=0;i<list.length;i++){if(typeof list[i]!=='string')return 'unweighted-only';if(!names.some(v=>v===list[i]))return 'unknown-vertex';if(list.slice(0,i).includes(list[i]))return 'duplicate-edge';}n+=list.length;}return n>32?'edge-limit':null;
}
export function enumerate(input){
  const error=contract(input);if(error)return {accepted:false,code:error};
  const paths=[];function extend(path){paths.push(path);for(const next of input.graph[path.at(-1)])if(!path.includes(next))extend([...path,next]);}extend([input.start]);
  const distances={};for(const v of Object.keys(input.graph)){const sizes=paths.filter(p=>p.at(-1)===v).map(p=>p.length-1);distances[v]=sizes.length?Math.min(...sizes):null;}
  const routes=paths.filter(p=>p.at(-1)===input.target),minimum=distances[input.target];return {accepted:true,distances,minimum,shortest:routes.filter(p=>p.length-1===minimum),simplePathCount:paths.length};
}
export function audit(result,assert){
  const o=enumerate(result.input);for(const mode of ['bfs','dfs']){const r=result[mode];assert(r.mode===mode,'mode');assert(r.accepted===o.accepted,'acceptance');if(!o.accepted){assert(r.code===o.code,'refusal code');assert(!r.trace,'rejected input has no traversal');continue;}
    assert(r.stopped===true,'terminated');assert(r.trace.length<=2+2*8+32,'finite trace');assert(r.trace[0].action==='start'&&r.trace.at(-1).action==='done','trace endpoints');assert(r.trace.at(-1).frontier.length===0,'frontier drained');
    const reachable=Object.keys(o.distances).filter(v=>o.distances[v]!==null);assert(JSON.stringify([...r.visited].sort())===JSON.stringify(reachable.sort()),'reachable set');assert(r.visited.length===new Set(r.visited).size,'each vertex marked once');assert(r.scanned===r.visited.reduce((n,v)=>n+result.input.graph[v].length,0),'each reachable edge scanned once');
    const discoveries=r.trace.filter(s=>['enqueue-mark','push-mark'].includes(s.action));assert(discoveries.length===r.visited.length-1,'one discovery per non-root');let old=[],oldParent={},scan=0;
    for(const s of r.trace){assert(s.index===r.trace.indexOf(s),'step index');assert(s.scanned>=scan&&s.scanned<=scan+1,'scan progression');scan=s.scanned;assert(s.visited.length===new Set(s.visited).size,'snapshot visited unique');assert(JSON.stringify(s.visited.slice(0,old.length))===JSON.stringify(old),'visited prefix');for(const [v,p]of Object.entries(oldParent))assert(s.parent[v]===p,'parent immutable');old=s.visited;oldParent=s.parent;
      assert(s.parent[result.input.start]===null&&s.depth[result.input.start]===0,'root contract');assert(Object.keys(s.parent).length===s.visited.length,'parent membership');assert(Object.keys(s.depth).length===s.visited.length,'depth membership');
      for(const v of s.visited){assert(Object.hasOwn(s.parent,v),'marked has parent');if(v!==result.input.start){assert(result.input.graph[s.parent[v]]?.includes(v),'parent follows actual edge');assert(s.depth[v]===s.depth[s.parent[v]]+1,'parent depth');}if(mode==='bfs')assert(s.depth[v]===o.distances[v],'BFS first discovery shortest');}
      const front=mode==='bfs'?s.frontier:s.frontier.map(f=>f.vertex);assert(front.length===new Set(front).size,'frontier no repeats');for(const v of front)assert(s.visited.includes(v),'marked before queued/pushed');if(mode==='bfs')for(let i=1;i<front.length;i++)assert(s.depth[front[i-1]]<=s.depth[front[i]],'queue layer order');else for(let i=0;i<s.frontier.length;i++){const f=s.frontier[i];assert(Number.isInteger(f.nextIndex)&&f.nextIndex>=0&&f.nextIndex<=result.input.graph[f.vertex].length,'frame cursor bounds');if(i)assert(s.parent[f.vertex]===s.frontier[i-1].vertex,'active stack parent chain');}
    }
    const last=r.trace.at(-1);for(const k of ['visited','parent','depth','scanned'])assert(JSON.stringify(r[k])===JSON.stringify(last[k]),'summary binds final trace '+k);
    if(o.minimum===null)assert(r.path===null&&r.length===null,'unreachable path');else{assert(Array.isArray(r.path)&&r.path[0]===result.input.start&&r.path.at(-1)===result.input.target,'path endpoints');assert(r.length===r.path.length-1,'edge count');assert(new Set(r.path).size===r.path.length,'simple returned path');for(let i=1;i<r.path.length;i++)assert(result.input.graph[r.path[i-1]].includes(r.path[i]),'path edge');for(let i=1;i<r.path.length;i++)assert(r.parent[r.path[i]]===r.path[i-1],'path parent binding');if(mode==='bfs')assert(r.length===o.minimum,'BFS shortest result');else assert(r.length>=o.minimum,'DFS valid, not shortest claim');}
  }
  if(result.input.id==='counterexample'){assert(JSON.stringify(result.bfs.path)==='["S","B","T"]','fixed BFS counterexample');assert(JSON.stringify(result.dfs.path)==='["S","A","C","T"]','fixed DFS counterexample');assert(result.dfs.length>o.minimum,'first path is not shortest');}
  if(result.input.id==='equal-paths'){assert(o.shortest.length===2,'two minimal routes');assert(result.bfs.parent.T==='A','fixed order tie break');}return o;
}
