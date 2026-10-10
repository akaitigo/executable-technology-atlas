"""Independent declarative window oracle. Does not import model or normalize."""
# Hand-calculated fixture expectations for window=30, threshold=3.
HAND = {'normal': {'arrival':['s1'],'event-time':['s1']}, 'late':{'arrival':[],'event-time':['s1']}, 'duplicate':{'arrival':[],'event-time':[]}, 'invalid':{'arrival':[],'event-time':[]}, 'boundary':{'arrival':['s1'],'event-time':['s1']}, 'outside':{'arrival':[],'event-time':[]}, 'other-user':{'arrival':[],'event-time':[]}}

def expected(rows, mode, window, threshold):
    # Separate field checks and id grouping; count directly per success, no failure buffer.
    valid=[]; ids={}
    for index,r in enumerate(rows):
        if not isinstance(r,dict) or sorted(r)!=['action','id','time','user']: continue
        if not isinstance(r['id'],str) or not 0<len(r['id'])<=32: continue
        if r['user'] not in ['mock-a','mock-b'] or r['action'] not in ['fail','success']: continue
        if isinstance(r['time'],bool) or not isinstance(r['time'],int) or r['time']<0 or r['time']>1000: continue
        if r['id'] in ids:
            if ids[r['id']]!=r: raise ValueError('conflict')
            continue
        ids[r['id']]=r
        valid.append((index,r))
    alerts=[]; windows=[]
    successes=[(i,r) for i,r in valid if r['action']=='success']
    if mode=='event-time': successes.sort(key=lambda pair:(pair[1]['time'],pair[1]['id']))
    for i,s in successes:
        failures=[r for j,r in valid if r['action']=='fail' and r['user']==s['user'] and 0<s['time']-r['time']<=window and (mode=='event-time' or j<i)]
        windows.append({'success':s['id'],'failureIds':sorted(r['id'] for r in failures),'count':len(failures)})
        if len(failures)>=threshold: alerts.append(s['id'])
    return {'alertIds':alerts,'windows':windows}
