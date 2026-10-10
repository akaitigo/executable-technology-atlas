import json,sys
ROUTES={'material-closure':'baseline','B-change':'B-changed','undeclared-B':'B-undeclared','graph-closure':'B-unreachable','unknown-node':'unknown-node','cycle':'cycle','read-failure':'read-failure'}
def route(t):return {'status':'supported','case':ROUTES[t]} if t in ROUTES else {'status':'unsupported','reason':'finite unsigned local artifact only; see README next coverage'}
if __name__=='__main__':print(json.dumps(route(sys.argv[1] if len(sys.argv)>1 else ''),ensure_ascii=False))
