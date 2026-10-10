import json,sys
SUPPORTED={'atomic-reload':'after-reload','last-known-good':'bad-type','between-reads':'between-reads','partial-window':'before-commit','json-refusal':'bad-syntax','read-failure':'read-failure'}
def route(topic):return {'status':'supported','case':SUPPORTED[topic]} if topic in SUPPORTED else {'status':'unsupported','reason':'finite synthetic unit only; see README next coverage'}
if __name__=='__main__':print(json.dumps(route(sys.argv[1] if len(sys.argv)>1 else ''),ensure_ascii=False))
