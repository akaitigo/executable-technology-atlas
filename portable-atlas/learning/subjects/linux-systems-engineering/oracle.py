"""Hand permissions matrix. No model import, shifts or bit operations."""
RIGHTS={'0':[],'1':['x'],'2':['w'],'3':['w','x'],'4':['r'],'5':['r','x'],'6':['r','w'],'7':['r','w','x']}
CLASS={'owner':('owner',0),'owner-group':('owner',0),'group':('group',1),'supplementary':('group',1),'other':('other',2)}
REQUESTS={'read':['r'],'write':['w'],'execute':['x'],'search':['x'],'read-write':['r','w']}
ACTORS={'owner':{'uid':1001,'gid':3001,'supplementary':[]},'group':{'uid':1002,'gid':2001,'supplementary':[]},'supplementary':{'uid':1002,'gid':3001,'supplementary':[2001]},'other':{'uid':1002,'gid':3001,'supplementary':[]},'owner-group':{'uid':1001,'gid':2001,'supplementary':[2001]},'root':{'uid':0,'gid':0,'supplementary':[]}}
def expected(mode,principal,operation,kind='file',security='none'):
    if principal=='root' or security!='none':return {'status':'rejected','selected':None,'allowed':None}
    selected,index=CLASS[principal];rights=RIGHTS[mode[index]];needs=REQUESTS[operation]
    return {'status':'decided','selected':selected,'allowed':all(right in rights for right in needs),'rights':rights,'needs':needs}
