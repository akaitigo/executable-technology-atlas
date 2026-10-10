"""Independent Python JSON/type oracle; not Swift execution or error-message emulation."""
import json,math
VARIANTS=('normal','eager-optional','defaulting')
def number(v):
 if type(v) is int:return -128<=v<=127
 return type(v) is float and math.isfinite(v) and v.is_integer() and -128<=v<=127
def expected(text,variant='normal'):
 try:data=json.loads(text,parse_constant=lambda s:(_ for _ in ()).throw(ValueError(s)))
 except (ValueError,TypeError):return {'status':'rejected','profile':None,'reason':'JSON syntax'}
 if type(data) is not dict:return {'status':'rejected','profile':None,'reason':'root object required'}
 fields=(('name',lambda v:type(v) is str,''),('age',number,0),('note',lambda v:type(v) is str,None))
 values={}
 for key,valid,default in fields:
  optional=key=='note' and variant=='normal';absent=key not in data;null=not absent and data[key] is None
  if optional and (absent or null):values[key]=None;continue
  if absent or null or not valid(data[key]):
   if variant=='defaulting':values[key]=default;continue
   return {'status':'rejected','profile':None,'reason':key+(':missing' if absent else ':null' if null else ':type/range')}
  values[key]=int(data[key]) if key=='age' else data[key]
 return {'status':'accepted','profile':values,'reason':None}
def projection(value):return {k:value[k] for k in ('status','profile')}
