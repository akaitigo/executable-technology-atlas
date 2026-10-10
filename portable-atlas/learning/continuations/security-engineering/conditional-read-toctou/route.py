import json,sys
ROUTES={'conditional-read':'unchanged','toctou-gap':'move-after-check','check-before-change':'move-before-check','payload-update':'payload-after-check','late-allow':'beta-after-check','unknown-actor':'unknown-actor','sql-error':'sql-error'}
def route(t):return {'status':'supported','case':ROUTES[t]} if t in ROUTES else {'status':'unsupported','reason':'finite synthetic SQLite only; see README remaining coverage'}
if __name__=='__main__':print(json.dumps(route(sys.argv[1] if len(sys.argv)>1 else ''),ensure_ascii=False))
