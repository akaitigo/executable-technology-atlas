#!/usr/bin/env python3
"""Atlas: emit each finite observation before continuing; never read expected.json."""
import hashlib,importlib.util,json,os,platform,resource,sys,traceback
from pathlib import Path
from compiler_vm import compile_tree,execute_vm
ROOT=Path(__file__).resolve().parent

def emit(record):
    print(json.dumps(record,ensure_ascii=False,separators=(',',':')),flush=True)

def main():
    resource.setrlimit(resource.RLIMIT_CPU,(2,2))
    spec=importlib.util.spec_from_file_location('atlas_prerequisite',ROOT/'inputs/prerequisite-language.py')
    language=importlib.util.module_from_spec(spec);spec.loader.exec_module(language)
    emit({'kind':'environment','project':'Atlas','python_version':sys.version,'python_executable':sys.executable,
          'platform':platform.platform(),'pid':os.getpid(),'nice':os.getpriority(os.PRIO_PROCESS,0),
          'cpu_limit_seconds':list(resource.getrlimit(resource.RLIMIT_CPU)),'workers_created':0})
    inputs=json.loads((ROOT/'inputs.json').read_text())
    for entry in inputs['normal']:
        tokens,_=language.tokenize(entry['expression'])
        tree=language.Parser(entry['expression'],tokens).parse()
        tree_trace=[]
        tree_value=language.evaluate(tree,tree_trace)
        compiled=compile_tree(tree)
        vm=execute_vm(compiled['constants'],compiled['code'])
        matched=vm['status']=='returned' and vm['value']==tree_value
        emit({'kind':'case','id':entry['id'],'classification':'normal' if matched else 'unexpected-mismatch',
              'expression':entry['expression'],'ast':tree,'tree_value':tree_value,'tree_trace':tree_trace,
              'compiled':compiled,'vm':vm,'tree_vm_equal':matched})
        if not matched:return 1
    for entry in inputs['rejections']:
        vm=execute_vm(entry['constants'],entry['code'])
        rejected=vm['status']=='rejected'
        emit({'kind':'case','id':entry['id'],'classification':'expected-rejection' if rejected else 'unexpected-acceptance',
              'constants':entry['constants'],'code':entry['code'],'vm':vm})
        if not rejected:return 1
    emit({'kind':'batch-complete','normal_count':5,'rejection_count':7,'retry_count':0})
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        emit({'kind':'producer-failure','type':type(error).__name__,'detail':str(error),'traceback':traceback.format_exc()})
        raise SystemExit(1)
