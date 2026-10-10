import json,sys
ROUTES={'pinned-rerun':'repeat-day1','new-version':'new-version','new-interval':'same-input-new-interval','same-label':'same-label-changed-input','artifact-binding':'corrupt-cache','latest-drift':'latest-changed-explicit-v1','refusal':'bad-input','read-failure':'read-failure'}
def route(topic):return {'status':'supported','case':ROUTES[topic]} if topic in ROUTES else {'status':'unsupported','reason':'finite local model only; see README next coverage'}
if __name__=='__main__':print(json.dumps(route(sys.argv[1] if len(sys.argv)>1 else ''),ensure_ascii=False))
