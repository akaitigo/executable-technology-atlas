import ctypes as C,ctypes.util
LIBRARY=ctypes.util.find_library('sqlite3');lib=C.CDLL(LIBRARY)
def bind(name,restype,args):
 f=getattr(lib,name);f.restype=restype;f.argtypes=args;return f
ptr=C.c_void_p;string=C.c_char_p;integer=C.c_int
callback=C.CFUNCTYPE(integer,ptr,integer,C.POINTER(string),C.POINTER(string))
open_db=bind('sqlite3_open_v2',integer,[string,C.POINTER(ptr),integer,string]);close_db=bind('sqlite3_close',integer,[ptr]);exec_db=bind('sqlite3_exec',integer,[ptr,string,callback,ptr,C.POINTER(string)]);free=bind('sqlite3_free',None,[ptr]);extended=bind('sqlite3_extended_errcode',integer,[ptr]);extended_on=bind('sqlite3_extended_result_codes',integer,[ptr,integer]);errmsg=bind('sqlite3_errmsg',string,[ptr]);autocommit=bind('sqlite3_get_autocommit',integer,[ptr]);txn=bind('sqlite3_txn_state',integer,[ptr,string]);version=bind('sqlite3_libversion',string,[]);source=bind('sqlite3_sourceid',string,[])
NAMES={0:'SQLITE_OK',5:'SQLITE_BUSY',517:'SQLITE_BUSY_SNAPSHOT',773:'SQLITE_BUSY_TIMEOUT'}
class Connection:
 def __init__(self,path):
  self.handle=ptr();rc=open_db(str(path).encode(),C.byref(self.handle),6,None)
  if rc:
   if self.handle:close_db(self.handle);self.handle=None
   raise RuntimeError('sqlite3_open_v2 failed code '+str(rc))
  if extended_on(self.handle,1):self.close();raise RuntimeError('extended_result_codes failed')
 def state(self):return {'autocommit':autocommit(self.handle),'txn_state':txn(self.handle,b'main')}
 def sql(self,text):
  rows=[]
  @callback
  def collect(ctx,n,values,names):
   rows.append([values[i].decode() if values[i] is not None else None for i in range(n)]);return 0
  message=string();rc=exec_db(self.handle,text.encode(),collect,None,C.byref(message));code=extended(self.handle);msg=message.value.decode() if message.value else errmsg(self.handle).decode()
  if message:free(C.cast(message,ptr))
  return {'sql':text,'rows':rows,'return_code':rc,'extended_code':code,'primary_code':code&255,'code_name':NAMES.get(code,'unmapped-code-'+str(code)),'message':msg,'state':self.state()}
 def close(self):
  if self.handle:
   rc=close_db(self.handle)
   if rc:raise RuntimeError('sqlite3_close failed '+str(rc))
   self.handle=None
