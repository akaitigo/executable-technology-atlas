import json,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
C=json.loads((ROOT/'contracts.json').read_text())
SQL_VERSION='UPDATE kv SET value=?, version=version+1 WHERE key=? AND version=?'
SQL_GENERATION='UPDATE kv SET value=?, version=version+1 WHERE key=? AND generation=? AND version=?'
class Refusal(ValueError):pass
def validate(r):
    if type(r['key']) is not str or r['key']!='k':raise Refusal('key-contract')
    if type(r['generation']) is not str or r['generation'] not in ('g1','g2'):raise Refusal('generation-contract')
    if type(r['version']) is not int:raise Refusal('version-type')
    if not 1<=r['version']<=999:raise Refusal('version-range')
    if type(r['value']) is not int:raise Refusal('value-type')
    if not 0<=r['value']<=999:raise Refusal('value-range')
def state(db):
    row=db.execute('SELECT key,generation,version,value FROM kv WHERE key=?',('k',)).fetchone()
    return dict(zip(('key','generation','version','value'),row)) if row else None
def request(g,v,x):return {'key':'k','generation':g,'version':v,'value':x}
def run(output):
    output=Path(output);rows=[]
    for scenario in C['cases']+C['refusals']+[C['sql_error_probe']]:
        name=scenario['id'];trace=[];steps=[];file=output/(name+'.sqlite');db=sqlite3.connect(str(file),isolation_level=None)
        db.set_trace_callback(trace.append)
        try:
            db.execute('CREATE TABLE kv(key TEXT PRIMARY KEY,generation TEXT NOT NULL,version INTEGER NOT NULL,value INTEGER NOT NULL)')
            def execute(label,sql,params):
                before=state(db);n=db.execute(sql,params).rowcount
                steps.append({'label':label,'sql':sql,'params':list(params),'rowcount':n,'before':before,'state':state(db)})
            execute('create-g1','INSERT INTO kv VALUES(?,?,?,?)',('k','g1',1,0))
            def cas(label,r,mode):
                validate(r);sql=SQL_VERSION if mode=='version' else SQL_GENERATION
                params=(r['value'],r['key'],r['version']) if mode=='version' else (r['value'],r['key'],r['generation'],r['version'])
                execute(label,sql,params)
            if name.startswith('refuse-'):
                count=len(trace);before=state(db);count=len(trace)
                try:cas('invalid-input',scenario['request'],'generation-version')
                except Refusal as e:reason=str(e)
                else:raise AssertionError('invalid input accepted')
                issued=trace[count:];final=state(db)
                row={'id':name,'label':scenario['label'],'status':'expected-refusal','reason':reason,'request':scenario['request'],'update_sql_issued':any(t.startswith('UPDATE') for t in issued),'before':before,'final':final,'steps':steps}
            elif name=='sql-error':
                before=state(db)
                try:db.execute(scenario['sql'])
                except sqlite3.OperationalError as e:error={'type':'OperationalError','message':str(e)}
                else:raise AssertionError('SQL error probe succeeded')
                row={'id':name,'label':'SQL構文errorと0行更新を分ける','status':'expected-sql-error','attempted_sql':scenario['sql'],'error':error,'rowcount':None,'before':before,'final':state(db),'steps':steps}
            else:
                mode=scenario['mode']
                if scenario['lifetime']=='same':
                    cas('fresh-v1',request('g1',1,5),mode);cas('old-v1',request('g1',1,1),mode);cas('fresh-v2',request('g1',2,6),mode)
                else:
                    execute('delete-g1','DELETE FROM kv WHERE key=?',('k',));execute('recreate-g2','INSERT INTO kv VALUES(?,?,?,?)',('k','g2',1,100));cas('old-g1-v1',request('g1',1,1),mode)
                    cas('fresh-g2',request('g2',2 if mode=='version' else 1,101),mode)
                row={'id':name,'label':scenario['label'],'status':'accepted-experiment','mode':mode,'lifetime':scenario['lifetime'],'old_request_rowcount':steps[-2]['rowcount'],'fresh_request_rowcount':steps[-1]['rowcount'],'steps':steps,'final':state(db)}
            row['sql_trace']=trace;row['database_file']=file.name;rows.append(row)
        finally:db.close()
    return {'rows':rows,'sqlite_version':sqlite3.sqlite_version,'schedule':'single connection per case, fixed sequential autocommit, synthetic non-reused g1/g2','claim':'finite local SQLite WHERE comparison; no distributed CAS, parallel locking or power-loss proof'}
if __name__=='__main__':print(json.dumps(run(sys.argv[1]),ensure_ascii=False))
