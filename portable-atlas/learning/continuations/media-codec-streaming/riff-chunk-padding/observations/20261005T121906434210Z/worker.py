#!/usr/bin/env python3
import hashlib,json,pathlib,struct,sys,wave
def parse(b,omit_pad=False):
 out={'accepted':False,'reason':None,'riffEnd':None,'chunks':[],'pcmHex':None,'samples':None}
 def reject(s):out['reason']=s;return out
 if len(b)<12 or b[:4]!=b'RIFF' or b[8:12]!=b'WAVE':return reject('unsupported-header')
 end=8+struct.unpack_from('<I',b,4)[0];out['riffEnd']=end
 if end!=len(b):return reject('riff-length-mismatch')
 off=12;fmt=None;pcm=None
 while off<end:
  if off+8>end:return reject('chunk-header-bounds')
  name=b[off:off+4].decode('latin1');size=struct.unpack_from('<I',b,off+4)[0];start=off+8;stop=start+size;pad=0 if omit_pad else size%2;nxt=stop+pad
  out['chunks'].append({'id':name,'headerOffset':off,'declaredSize':size,'dataStart':start,'dataEnd':stop,'padBytes':pad,'nextOffset':nxt,'actualAvailable':max(0,min(size,end-start)),'headerHex':b[off:off+8].hex()})
  if stop>end:return reject('chunk-payload-bounds')
  if nxt>end:return reject('chunk-pad-bounds')
  if name=='fmt ':
   if size!=16:return reject('unsupported-fmt-size')
   fmt=struct.unpack('<HHIIHH',b[start:stop])
  elif name=='data':
   if pcm is not None:return reject('duplicate-data')
   pcm=b[start:stop]
  off=nxt
 if fmt!=(1,1,8000,16000,2,16):return reject('unsupported-mono16-format')
 if pcm is None:return reject('missing-data')
 if len(pcm)%2:return reject('unaligned-pcm')
 out.update(accepted=True,pcmHex=pcm.hex(),samples=list(struct.unpack('<'+'h'*(len(pcm)//2),pcm)));return out
def wave_read(path):
 out={'status':None,'errorClass':None,'error':None}
 try:
  with wave.open(str(path),'rb') as w:
   frames=w.getnframes();request=min(frames+1,16);pcm=w.readframes(request)
   out.update(status='read',params={'channels':w.getnchannels(),'sampleWidth':w.getsampwidth(),'rate':w.getframerate(),'declaredFrames':frames},requestedFrames=request,returnedBytes=len(pcm),pcmHex=pcm.hex(),declaredFrameBytes=frames*w.getsampwidth()*w.getnchannels(),completeDeclaredFrames=len(pcm)==frames*w.getsampwidth()*w.getnchannels(),samples=list(struct.unpack('<'+'h'*(len(pcm)//2),pcm)) if len(pcm)%2==0 else None)
 except Exception as e:out.update(status='exception',errorClass=type(e).__name__,error=str(e))
 return out
def main():
 p=pathlib.Path(sys.argv[1])
 with p.open('rb') as f:b=f.read(1025)
 if len(b)>1024:print(json.dumps({'refusal':'fixture-too-large'}));return 2
 strict=parse(b);out={'fileBytes':len(b),'fileSha256':hashlib.sha256(b).hexdigest(),'fileHex':b.hex(),'strict':strict,'omitPaddingBug':parse(b,True),'wave':wave_read(p)}
 print(json.dumps(out));return 0 if strict['accepted'] else 2
if __name__=='__main__':sys.exit(main())
