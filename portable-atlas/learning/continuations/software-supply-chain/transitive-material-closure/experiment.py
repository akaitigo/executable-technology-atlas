import hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
class Refused(Exception):pass
def sha(b):return hashlib.sha256(b).hexdigest()
def closure(graph,trace):
 if type(graph) is not dict or set(graph)!={'root','nodes'} or graph['root'] not in graph['nodes']:raise Refused('graph-contract')
 nodes=graph['nodes'];visiting=set();done=set()
 def visit(n):
  if n not in nodes:raise Refused('unknown-node')
  if n in visiting:raise Refused('cycle')
  if n in done:return
  if type(nodes[n]) is not dict or set(nodes[n])!={'file','deps'} or type(nodes[n]['deps']) is not list:raise Refused('node-contract')
  visiting.add(n);trace.append({'event':'graph-enter','node':n})
  for dep in nodes[n]['deps']:visit(dep)
  visiting.remove(n);done.add(n);trace.append({'event':'graph-leave','node':n})
 visit(graph['root']);return sorted(done)
def run(spec,baseline):
 trace=[];reach=None;materials={};artifact=None;declared=None;direct=None;error=None;status='observed'
 try:
  trace.append({'event':'json-read','fixture':spec['graph']});graph=json.loads((ROOT/'fixtures'/spec['graph']).read_text());reach=closure(graph,trace);direct=graph['nodes'][graph['root']]['deps']
  chunks=[]
  for name in reach:
   file=graph['nodes'][name]['file'];trace.append({'event':'material-read-attempt','node':name,'fixture':file})
   try:b=(ROOT/'fixtures'/file).read_bytes()
   except OSError:raise OSError('material-read-failed:'+name) from None
   materials[name]={'sha256':sha(b),'size':len(b),'hex':b.hex()};chunks.append(name.encode()+b':'+str(len(b)).encode()+b':'+b);trace.append({'event':'material-read','node':name,'sha256':sha(b),'size':len(b)})
  output=b''.join(chunks);artifact={'hex':output.hex(),'ascii':output.decode('ascii'),'sha256':sha(output),'size':len(output)};trace.append({'event':'artifact-built','sha256':artifact['sha256']})
  trace.append({'event':'json-read','fixture':spec['declared']});declared=json.loads((ROOT/'fixtures'/spec['declared']).read_text())
  if type(declared) is not dict or any(type(k) is not str or type(v) is not str for k,v in declared.items()):raise Refused('declaration-contract')
  if set(declared)!=set(reach):normal={'decision':'refuse','reason':'declared-material-set','missing':sorted(set(reach)-set(declared)),'extra':sorted(set(declared)-set(reach))}
  elif set(reach)!=set(baseline):normal={'decision':'refuse','reason':'expected-closure','missing':sorted(set(baseline)-set(reach)),'extra':sorted(set(reach)-set(baseline))}
  else:
   mismatch=[n for n in reach if declared[n]!=materials[n]['sha256'] or materials[n]['sha256']!=baseline[n]]
   normal={'decision':'deny' if mismatch else 'allow','reason':'material-digest' if mismatch else 'all-materials-match','mismatched':mismatch}
  faulty={'decision':'allow' if direct==['A'] else 'deny','reason':'direct-name-match' if direct==['A'] else 'direct-name-mismatch'}
  trace.append({'event':'consumer-check','normal':normal['decision'],'faulty':faulty['decision']})
 except Refused as e:status='expected-refusal';error=str(e);normal={'decision':'refuse','reason':error};faulty=dict(normal);artifact=None
 except OSError as e:status='execution-error';error=str(e);normal={'decision':'error','reason':error};faulty=dict(normal);artifact=None
 return {'status':status,'reachable':reach,'direct_names':direct,'materials':materials,'declared':declared,'artifact':artifact,'normal':normal,'faulty':faulty,'error':error,'trace':trace}
def main():
 baseline=json.loads((ROOT/'fixtures/baseline-materials.json').read_text());specs=json.loads((ROOT/'contracts.json').read_text())['cases']
 print(json.dumps({'rows':[{'id':s['id'],**run(s,baseline)} for s in specs]},ensure_ascii=False))
if __name__=='__main__':main()
