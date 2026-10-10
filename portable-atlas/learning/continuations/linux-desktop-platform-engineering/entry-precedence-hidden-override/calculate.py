import hashlib
ID='org.example.Mock.desktop'
def parse(text):
    lines=text.splitlines()
    if not lines or lines[0]!='[Desktop Entry]':raise ValueError('GROUP_SUBSET')
    fields={}
    for line in lines[1:]:
        if not line:continue
        if '=' not in line:raise ValueError('KEY_SUBSET')
        key,value=line.split('=',1)
        if key in fields:raise ValueError('DUPLICATE_KEY')
        if key not in ['Type','Name','Exec','Hidden']:raise ValueError('KEY_SUBSET')
        fields[key]=value
    if fields.get('Type')!='Application' or not fields.get('Name') or fields.get('Exec')!='atlas-mock':raise ValueError('REQUIRED_SUBSET')
    if fields.get('Hidden','false') not in ['true','false']:raise ValueError('INVALID_BOOLEAN')
    return fields
def resolve(root,f):
    trace=[];base=dict(selected_source=None,suppressed=False,count=0,visited=[],trace=trace)
    if f['entry_id']!=ID:return dict(base,status='INPUT_REJECTED',reason='OUTSIDE_ID',resolution_started=False)
    base['resolution_started']=True;skipped=False
    for source in ['user','system']:
        base['visited'].append(source);p=root/source/'applications'/ID
        if not p.exists():trace.append(dict(source=source,path=source+'/applications/'+ID,exists=False));continue
        data=p.read_bytes();row=dict(source=source,path=source+'/applications/'+ID,exists=True,raw=data.decode(),sha256=hashlib.sha256(data).hexdigest());trace.append(row)
        try:fields=parse(row['raw']);row['fields']=fields
        except ValueError as error:return dict(base,status='INPUT_REJECTED',reason=str(error))
        if fields.get('Hidden','false')=='true':
            if f['mode']=='skip-hidden':row['action']='BAD_SKIP';skipped=True;continue
            row['action']='SUPPRESS';return dict(base,status='SUPPRESSED',selected_source=source,suppressed=True)
        row['action']='SELECT';return dict(base,status='BAD_RESURRECTED' if skipped else 'SELECTED',selected_source=source,count=1,name=fields['Name'])
    return dict(base,status='NOT_FOUND')
