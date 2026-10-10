"""Finite quote/backslash argument-tail model; NOT CommandLineToArgvW or CRT."""
SPACE=' \t'
def validate(spec):
 if type(spec) is not dict or set(spec)!= {'tail'}:return 'input_keys'
 text=spec['tail']
 if type(text) is not str:return 'tail_string'
 if len(text)>128:return 'tail_max128'
 if any(not (32<=ord(c)<=126 or c=='\t') for c in text):return 'ASCII_printable_or_tab_only'
 return None

def state(quoted,current,pending,args,active):return dict(quoted=quoted,current=current,pending_backslashes=pending,args=list(args),active=active)
def parse_tail(text):
 quoted=False;current='';pending=0;args=[];active=False;trace=[];last_quote=None
 for index,c in enumerate(text):
  before=state(quoted,current,pending,args,active);rule='literal'
  if c=='\\':pending+=1;active=True;rule='backslash_pending'
  elif c=='"':
   if pending%2==0:
    if last_quote and last_quote['index']==index-1:
     empty_pair=last_quote['empty_open'] and (index+1==len(text) or text[index+1] in SPACE)
     if not empty_pair:return dict(status='rejected',phase='subset',args=None,trace=trace,state=before,fault=dict(reason='adjacent_syntactic_quotes_outside_subset',index=index))
    last_quote=dict(index=index,empty_open=not quoted and not active and not pending)
    current+='\\'*(pending//2);quoted=not quoted;rule='even_backslashes_toggle_quote'
   else:current+='\\'*(pending//2)+'"';rule='odd_backslashes_literal_quote';last_quote=None
   pending=0;active=True
  else:
   current+='\\'*pending;pending=0
   if c in SPACE and not quoted:
    if active:args.append(current)
    current='';active=False;rule='outside_whitespace_delimiter'
   else:current+=c;active=True;rule='inside_whitespace_literal' if c in SPACE else 'literal'
  after=state(quoted,current,pending,args,active);trace.append(dict(index=index,char=c,rule=rule,before=before,after=after))
 before=state(quoted,current,pending,args,active);current+='\\'*pending;pending=0
 if quoted:
  after=state(quoted,current,pending,args,active);trace.append(dict(index=len(text),char='<EOF>',rule='subset_unbalanced_quote',before=before,after=after))
  return dict(status='rejected',phase='subset',args=None,trace=trace,state=after,fault=dict(reason='unbalanced_quote_outside_subset',index=len(text)))
 if active:args.append(current)
 after=state(quoted,'',pending,args,False);trace.append(dict(index=len(text),char='<EOF>',rule='finish_argument',before=before,after=after))
 return dict(status='accepted',phase='model',args=args,trace=trace,state=after,fault=None)

def simple_split(text):
 # Real Python str.split used as deliberate bad argument parser. Trace is explanatory.
 args=[];current='';trace=[]
 for i,c in enumerate(text):
  before={'current':current,'args':list(args)}
  if c in SPACE:
   if current:args.append(current)
   current='';rule='split_whitespace'
  else:current+=c;rule='literal_ignores_quote_backslash'
  trace.append(dict(index=i,char=c,rule=rule,before=before,after={'current':current,'args':list(args)}))
 if current:args.append(current)
 trace.append(dict(index=len(text),char='<EOF>',rule='finish_split',before={'current':current,'args':list(args[:-1] if current else args)},after={'current':'','args':list(args)}))
 assert args==text.split()
 return dict(status='accepted',phase='intentional_bad_model',args=args,trace=trace,fault=None)

def analyze(spec):
 reason=validate(spec)
 if reason:return dict(status='rejected',phase='input',reason=reason,variants={})
 normal=parse_tail(spec['tail']);bad=simple_split(spec['tail'])
 return dict(status=normal['status'],phase=normal['phase'],variants={'subset':normal,'simple-split':bad})
