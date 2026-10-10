#!/usr/bin/env python3
"""Atlas: bounded saved-string tests only; no producer, browser or host process query."""
import ast,copy,hashlib,json,os
from pathlib import Path
from resource_parse import parse_processes
from resource_gate import decide
from priority_launcher import priority_gate
ROOT=Path(__file__).resolve().parent

def main():
 p=json.loads((ROOT/'browser-policy.json').read_text());own=123456
 lines=['%d %d 0.0 1024 %s %s'%(e['pid'],e['ppid'],e['lstart'],e['comm']) for e in p['identities']]
 lines.append('%d 1 0.0 1024 Wed Oct 7 03:55:46 2026 /usr/bin/python3'%own);text='\n'.join(lines)
 proc=parse_processes(text,0,own)
 base={'cpu_count':12,'loadavg':[3,3,3],'summary':{'idle_percent':80,'memory_free_percent':50,'available_memory_estimate_gib':4,'read_success':True},'process_observation':proc,'coordination':{'other_target_count':0,'slot_reference':'saved test: exclusive target slot','root_gui_idle':True,'root_gui_idle_reference':'saved test: parent confirms idle'}}
 rows=[]
 def test(name,change,wanted):
  r=copy.deepcopy(base);change(r);decision=decide(r);rows.append({'name':name,'expected':wanted,'actual':decision['allowed'],'passed':decision['allowed']==wanted,'input':r,'decision':decision})
 test('exact 57 idle identities',lambda r:None,True)
 test('CPU exactly 1 allowed',lambda r:r['process_observation']['browsers'][0].__setitem__('cpu_percent_one_core',1),True)
 test('CPU over 1',lambda r:r['process_observation']['browsers'][0].__setitem__('cpu_percent_one_core',1.01),False)
 test('PID reused with new start',lambda r:r['process_observation']['browsers'][0].__setitem__('lstart','Wed Oct 7 04:55:46 2026'),False)
 test('parent PID mismatch',lambda r:r['process_observation']['browsers'][0].__setitem__('ppid',42),False)
 test('executable mismatch',lambda r:r['process_observation']['browsers'][0].__setitem__('command','/tmp/another-headless_shell'),False)
 test('required root missing',lambda r:r.__setitem__('process_observation',parse_processes('\n'.join(x for x in lines if not x.startswith('90274 ')),0,own)),False)
 test('nonroot known process absent',lambda r:r.__setitem__('process_observation',parse_processes('\n'.join(x for x in lines if not x.startswith('665 ')),0,own)),True)
 test('sum exactly 2',lambda r:[x.__setitem__('cpu_percent_one_core',1) for x in r['process_observation']['browsers'][:2]],True)
 test('sum over 2',lambda r:[x.__setitem__('cpu_percent_one_core',0.8) for x in r['process_observation']['browsers'][:3]],False)
 test('PID reused to non-browser executable',lambda r:r.__setitem__('process_observation',parse_processes(text.replace(p['identities'][0]['comm'],'/usr/bin/unrelated'),0,own)),False)
 test('extra browser row',lambda r:r['process_observation']['browsers'].append({**r['process_observation']['browsers'][0],'pid':42}),False)
 test('GUI idle unknown',lambda r:r['coordination'].__setitem__('root_gui_idle',None),False)
 test('no slot',lambda r:r['coordination'].__setitem__('slot_reference',''),False)
 test('other target active',lambda r:r['coordination'].__setitem__('other_target_count',1),False)
 test('load at 6',lambda r:r['loadavg'].__setitem__(0,6),False)
 test('idle below 60',lambda r:r['summary'].__setitem__('idle_percent',59),False)
 test('aggregate over 400 although idle above 60',lambda r:r['summary'].__setitem__('idle_percent',66),False)
 test('free below 40',lambda r:r['summary'].__setitem__('memory_free_percent',39),False)
 test('available below 2GiB',lambda r:r['summary'].__setitem__('available_memory_estimate_gib',1.99),False)
 test('memory unknown',lambda r:r['summary'].__setitem__('memory_free_percent',None),False)
 test('known active compiler',lambda r:r['process_observation']['heavy'].append({'command':'/usr/bin/clang','cpu_percent_one_core':30}),False)
 for name,source,code in [('ps empty','',0),('ps mixed malformed',text+'\nbad line',0),('ps failed',text,1),('self missing','\n'.join(lines[:-1]),0),('duplicate PID',text+'\n'+lines[0],0)]:
  test(name,lambda r,s=source,c=code:r.__setitem__('process_observation',parse_processes(s,c,own)),False)
 for browser in ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','/Applications/Firefox.app/Contents/MacOS/firefox','/System/Applications/Safari.app/Contents/MacOS/Safari','/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge','/Applications/Brave Browser.app/Contents/MacOS/Brave Browser','/Applications/Opera.app/Contents/MacOS/Opera','/System/Library/Frameworks/WebKit.framework/XPCServices/com.apple.WebKit.WebContent.xpc/Contents/MacOS/com.apple.WebKit.WebContent']:
  added=text+'\n42 1 0.0 1024 Wed Oct 7 03:55:46 2026 '+browser
  test('extra known browser: '+browser,lambda r,s=added:r.__setitem__('process_observation',parse_processes(s,0,own)),False)
 priority=[]
 def case(name,values,setter,wanted):
  iterator=iter(values);r=priority_gate(lambda *_:next(iterator),setter);priority.append({'name':name,'record':r,'expected':wanted,'passed':r['verified_before_exec']==wanted})
 case('actual value confirmed',[0,10],lambda *_:None,True)
 case('silently ineffective set',[0,0],lambda *_:None,False)
 def denied(*_):raise PermissionError('saved simulation')
 case('set denied',[0],denied,False)
 syntax=[]
 for f in ROOT.glob('*.py'):ast.parse(f.read_text(),filename=str(f));syntax.append({'path':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
 result={'project':'Atlas','scope':'saved process strings and injected priority callbacks; not a host resource read or target execution','passed':all(r['passed'] for r in rows+priority),'resource_cases':rows,'priority_cases':priority,'syntax':syntax,'target_starts':0,'browser_starts':0,'host_process_queries':0}
 d=ROOT/'records/preflight';d.mkdir(exist_ok=True);(d/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'resource_cases':len(rows),'priority_cases':len(priority),'syntax_files':len(syntax),'target_starts':0}));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
