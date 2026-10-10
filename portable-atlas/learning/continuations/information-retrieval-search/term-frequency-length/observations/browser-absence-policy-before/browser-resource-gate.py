"""Atlas: read aggregate resources; narrowly classify one known idle JVM without touching it."""
import os,subprocess,json,datetime,re,hashlib,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def classify_candidates(rows,policy):
 found=[]
 for row in rows:
  allowed=policy['known_idle_exception']
  if row['pid']!=allowed['pid'] and not any(t in row['comm'].lower() for t in ['chrome-headless-shell','playwright','flutter_tester','java']):continue
  same=all(row.get(k)==allowed[k] for k in ['pid','ppid','lstart','comm'])
  idle=same and math.isfinite(row['cpu']) and 0<=row['cpu']<=allowed['cpu_percent_at_most']
  found.append({**row,'blocking':not idle,'classification':allowed['classification'] if idle else '未確認または稼働候補。開始しない'})
 return found

def main():
 stamp=datetime.datetime.now(datetime.timezone.utc);policy=json.loads((ROOT/'browser-gate-policy.json').read_text());j={'title':'Atlas 検索計算の資源確認','at_utc':stamp.isoformat(),'cpu_count':os.cpu_count(),'gate_source_sha256':sha(Path(__file__)),'gate_policy_sha256':sha(ROOT/'browser-gate-policy.json'),'headroom':False,'root_slot_still_required':True,'processes_modified':False,'scope':'aggregate, binary identity and start time; arguments not collected'}
 try:
  p=subprocess.run(['/bin/ps','-axo','pid=,ppid=,pcpu=,lstart=,comm='],capture_output=True,text=True,timeout=5);p.check_returncode();rows=[]
  for line in p.stdout.splitlines():
   v=line.strip().split(None,8)
   if len(v)!=9:raise ValueError('ps identity fields not observed')
   cpu=float(v[2])
   if not math.isfinite(cpu) or cpu<0:raise ValueError('invalid process CPU')
   rows.append({'pid':int(v[0]),'ppid':int(v[1]),'cpu':cpu,'lstart':' '.join(v[3:8]),'comm':v[8]})
  candidates=classify_candidates(rows,policy);aggregate=sum(x['cpu'] for x in rows)
  m=subprocess.run(['/usr/bin/memory_pressure','-Q'],capture_output=True,text=True,timeout=5);m.check_returncode();free=int(re.search(r'free percentage: (\d+)%',m.stdout).group(1));load=os.getloadavg()
  j.update(load=load,aggregate_cpu_percent=aggregate,runtime_candidates=candidates,memory_free_percent=free,limits={k:policy[k] for k in ['load_1m_less_than','aggregate_cpu_less_than','memory_free_percent_at_least']})
  j['headroom']=any(x['pid']==policy['known_idle_exception']['pid'] and not x['blocking'] for x in candidates) and not any(x['blocking'] for x in candidates) and load[0]<policy['load_1m_less_than'] and aggregate<policy['aggregate_cpu_less_than'] and free>=policy['memory_free_percent_at_least']
 except Exception as e:j['error']={'name':type(e).__name__,'message':str(e)}
 path=ROOT/'observations'/('resources-'+stamp.strftime('%Y%m%dT%H%M%S%fZ')+'.json');path.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(path.relative_to(ROOT)),**j},ensure_ascii=False));return 0 if j['headroom'] else 1
if __name__=='__main__':raise SystemExit(main())
