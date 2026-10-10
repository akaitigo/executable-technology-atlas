"""Pre-execution conditions, independent of certificate parsing and OpenSSL output."""
CONDITIONS={
 'normal':{'leaf':'good','ca':'a','time':'midday','chain':True,'name':True,'purpose':True,'timeValid':True,'strict':True,'noName':True,'chainOnly':True,'error':None},
 'wrong-san':{'leaf':'wrong-san','ca':'a','time':'midday','chain':True,'name':False,'purpose':True,'timeValid':True,'strict':False,'noName':True,'chainOnly':True,'error':62},
 'untrusted':{'leaf':'good','ca':'b','time':'midday','chain':False,'name':True,'purpose':True,'timeValid':True,'strict':False,'noName':False,'chainOnly':False,'error':20},
 'wrong-eku':{'leaf':'client','ca':'a','time':'midday','chain':True,'name':True,'purpose':False,'timeValid':True,'strict':False,'noName':False,'chainOnly':True,'error':26},
 'before-start':{'leaf':'good','ca':'a','time':'before-start','chain':True,'name':True,'purpose':True,'timeValid':False,'strict':False,'noName':False,'chainOnly':False,'error':9},
 'at-start':{'leaf':'good','ca':'a','time':'start','chain':True,'name':True,'purpose':True,'timeValid':True,'strict':True,'noName':True,'chainOnly':True,'error':None},
 'before-end':{'leaf':'good','ca':'a','time':'before-end','chain':True,'name':True,'purpose':True,'timeValid':True,'strict':True,'noName':True,'chainOnly':True,'error':None},
 'at-end':{'leaf':'good','ca':'a','time':'end','chain':True,'name':True,'purpose':True,'timeValid':False,'strict':False,'noName':False,'chainOnly':False,'error':10},
 'after-end':{'leaf':'good','ca':'a','time':'after-end','chain':True,'name':True,'purpose':True,'timeValid':False,'strict':False,'noName':False,'chainOnly':False,'error':10}}
TIMES={'before-start':1791158399,'start':1791158400,'midday':1791201600,'before-end':1791244799,'end':1791244800,'after-end':1791244801}
FIELDS={'good':{'san':'api.atlas.invalid','eku':'TLS Web Server Authentication'},'wrong-san':{'san':'other.atlas.invalid','eku':'TLS Web Server Authentication'},'client':{'san':'api.atlas.invalid','eku':'TLS Web Client Authentication'}}
