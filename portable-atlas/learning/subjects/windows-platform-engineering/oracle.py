"""Independent manual table lookup plus closed-form parity vectors; no parser import."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def expected(id):return json.loads((ROOT/'hand-table.json').read_text())['vectors'][id]
def parity_vectors():
 out=[]
 for inside in (False,True):
  for n in range(13):
   slashes='\\'*n;half='\\'*(n//2)
   if inside:
    if n%2:text='"pre'+slashes+'"post next" end';args=['pre'+half+'"post next','end']
    else:text='"pre'+slashes+'"post next';args=['pre'+half+'post','next']
   else:
    if n%2:text='pre'+slashes+'"post next';args=['pre'+half+'"post','next']
    else:text='pre'+slashes+'"post next" end';args=['pre'+half+'post next','end']
   out.append(dict(id=f'parity-{inside}-{n}',input={'tail':text},args=args,inside=inside,backslashes=n))
 for n in range(13):out.append(dict(id='literal-run-'+str(n),input={'tail':'pre'+'\\'*n+'post next'},args=['pre'+'\\'*n+'post','next'],backslashes=n))
 return out
