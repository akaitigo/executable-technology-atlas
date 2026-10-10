// 独自制作。有限・無重み・有向graph。全reachableを探索し、最初のparentを保持する。
export function validate(input){
  const g=input?.graph,fail=(code)=>({accepted:false,code});
  if(!g||typeof g!=='object'||Array.isArray(g))return fail('graph-object');
  const vertices=Object.keys(g);if(vertices.length<1||vertices.length>8||vertices.some(v=>!(/^[A-Z][A-Z0-9]{0,2}$/).test(v)))return fail('vertices');
  if(!vertices.includes(input.start)||!vertices.includes(input.target))return fail('endpoint');
  let edges=0;for(const v of vertices){if(!Array.isArray(g[v]))return fail('adjacency');if(g[v].some(w=>typeof w!=='string'))return fail('unweighted-only');if(g[v].some(w=>!vertices.includes(w)))return fail('unknown-vertex');if(new Set(g[v]).size!==g[v].length)return fail('duplicate-edge');edges+=g[v].length;}
  if(edges>32)return fail('edge-limit');return {accepted:true,vertices,edges};
}
export function traverse(input,mode){
  if(!['bfs','dfs'].includes(mode))throw new Error('mode');const contract=validate(input);if(!contract.accepted)return {mode,...contract};
  const {graph:g,start:s,target:t}=input,parent={[s]:null},depth={[s]:0},visited=[s],trace=[],frontier=mode==='bfs'?[s]:[{vertex:s,nextIndex:0}];let scanned=0,current=null;
  const emit=(action,edge=null)=>trace.push({index:trace.length,action,edge,current,frontier:structuredClone(frontier),visited:[...visited],parent:{...parent},depth:{...depth},scanned});
  const discover=(u,v)=>{parent[v]=u;depth[v]=depth[u]+1;visited.push(v);};emit('start');
  if(mode==='bfs')while(frontier.length){current=frontier.shift();emit('dequeue');for(const v of g[current]){scanned++;if(Object.hasOwn(parent,v))emit('skip-visited',[current,v]);else{discover(current,v);frontier.push(v);emit('enqueue-mark',[current,v]);}}}
  else while(frontier.length){const frame=frontier.at(-1);current=frame.vertex;if(frame.nextIndex===g[current].length){frontier.pop();emit('return');continue;}const v=g[current][frame.nextIndex++];scanned++;if(Object.hasOwn(parent,v))emit('skip-visited',[current,v]);else{discover(current,v);frontier.push({vertex:v,nextIndex:0});emit('push-mark',[current,v]);}}
  current=null;emit('done');let path=null;if(Object.hasOwn(parent,t)){path=[];for(let v=t;v!==null;v=parent[v])path.unshift(v);}
  return {mode,accepted:true,vertices:contract.vertices,path,length:path===null?null:path.length-1,visited,parent,depth,scanned,trace,stopped:true};
}
export function run(input){return {input:structuredClone(input),bfs:traverse(input,'bfs'),dfs:traverse(input,'dfs')};}
