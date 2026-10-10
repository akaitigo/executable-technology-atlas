#!/usr/bin/env python3
import hashlib,json,pathlib,struct,wave
ROOT=pathlib.Path(__file__).resolve().parent
FMT='666d74201000000001000100401f0000803e000002001000'
PCM='e80318fcff7f';DATA='6461746106000000'+PCM;JUNK='4a554e4b0300000058595a00'
HEX={'base':'524946462a00000057415645'+FMT+DATA,'odd-junk':'524946463600000057415645'+FMT+JUNK+DATA,'even-junk':'524946463600000057415645'+FMT+'4a554e4b040000005758595a'+DATA,'riff-oversize':'52494646e803000057415645'+FMT+JUNK+DATA,'chunk-oversize':'524946463600000057415645'+FMT+JUNK+'646174610a000000'+PCM,'short-data':'524946463400000057415645'+FMT+JUNK+'6461746106000000e80318fc','missing-pad':'524946463500000057415645'+FMT+'4a554e4b0300000058595a'+DATA}
# 手書きoffset、payload endとpadを独立固定。producerをimportしない。
A=['fmt ',12,16,20,36,0,36];D=['data',48,6,56,62,0,62]
SPECS={'base':(50,50,True,None,[A,['data',36,6,44,50,0,50]]),'odd-junk':(62,62,True,None,[A,['JUNK',36,3,44,47,1,48],D]),'even-junk':(62,62,True,None,[A,['JUNK',36,4,44,48,0,48],D]),'riff-oversize':(62,1008,False,'riff-length-mismatch',[]),'chunk-oversize':(62,62,False,'chunk-payload-bounds',[A,['JUNK',36,3,44,47,1,48],['data',48,10,56,66,0,66]]),'short-data':(60,60,False,'chunk-payload-bounds',[A,['JUNK',36,3,44,47,1,48],D]),'missing-pad':(61,61,False,'chunk-payload-bounds',[A,['JUNK',36,3,44,47,1,48],['ata\x06',48,3892314112,56,3892314168,0,3892314168]])}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check_wave(path,saved):
 # 実libraryのread/exceptionを別に再観測。strictの成功表へ読み替えない。
 try:
  with wave.open(str(path),'rb') as w:
   channels,width,rate,frames=w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes();request=min(frames+1,16);b=w.readframes(request)
   assert saved['status']=='read' and saved['error'] is None and saved['errorClass'] is None
   assert saved['params']==dict(channels=channels,sampleWidth=width,rate=rate,declaredFrames=frames)
   assert saved['requestedFrames']==request and saved['returnedBytes']==len(b) and saved['pcmHex']==b.hex()
   assert saved['declaredFrameBytes']==frames*width*channels and saved['completeDeclaredFrames'] is (len(b)==frames*width*channels)
   samples=list(struct.unpack('<'+'h'*(len(b)//2),b)) if len(b)%2==0 else None;assert saved['samples']==samples
 except (wave.Error,EOFError,RuntimeError) as e:assert saved['status']=='exception' and saved['errorClass']==type(e).__name__ and saved['error']==str(e),'actual wave exception'
def check(run):
 d=json.loads((run/'result.json').read_text());assert json.loads((run/'stdout.json').read_text())==d
 for n,h in json.loads((run/'artifacts.json').read_text()).items():assert (run/n).stat().st_size==h['bytes'] and digest(run/n)==h['sha256'],n
 for n,h in d['sourceHashes'].items():assert digest(ROOT/n)==h,n
 assert digest(run/'worker.py')==digest(ROOT/'worker.py') and digest(run/'oracle.json')==digest(ROOT/'oracle.json');prior=json.loads((run/'oracle.json').read_text())
 assert prior['pcmHex']==PCM and prior['samples']==[1000,-1000,32767]
 assert [c['id'] for c in d['cases']]==list(SPECS)
 for c in d['cases']:
  n=c['id'];size,end,accepted,reason,chunks=SPECS[n];folder=run/n;b=(folder/'input.wav').read_bytes();o=c['observation'];s=o['strict']
  assert b.hex()==HEX[n] and len(b)==size and size<=62,'independent fixture bytes';assert c['argv']==['python3','-B','worker.py',n+'/input.wav']
  assert c['inputSha256']==o['fileSha256']==digest(folder/'input.wav') and o['fileBytes']==size and o['fileHex']==HEX[n]
  assert c['stdout']==(folder/'stdout.json').read_text() and json.loads(c['stdout'])==o and c['stderr']==(folder/'stderr.txt').read_text()==''
  assert c['exitCode']==(0 if accepted else 2) and s['accepted'] is accepted and s['reason']==reason,'strict acceptance literal';assert s['riffEnd']==end
  table=[[x['id'],x['headerOffset'],x['declaredSize'],x['dataStart'],x['dataEnd'],x['padBytes'],x['nextOffset']] for x in s['chunks']];assert table==chunks,'hand offset table'
  p=prior['cases'][n];assert [p['fileBytes'],p['riffEnd'],p['strictAccepted'],p.get('reason'),p['chunks']]==[size,end,accepted,reason,chunks],'prior oracle literal'
  for x in s['chunks']:assert x['headerHex']==b[x['headerOffset']:x['headerOffset']+8].hex() and x['actualAvailable']==max(0,min(x['declaredSize'],end-x['dataStart']))
  if accepted:assert s['pcmHex']==PCM and s['samples']==[1000,-1000,32767],'PCM literal'
  else:assert s['pcmHex'] is None and s['samples'] is None
  bug=o['omitPaddingBug']
  if n=='odd-junk':assert bug['accepted'] is False and bug['reason']=='chunk-payload-bounds' and bug['chunks'][1]['nextOffset']==47 and bug['chunks'][2]['headerOffset']==47 and bug['chunks'][2]['id']=='\x00dat' and bug['chunks'][2]['declaredSize']==1633,'omitted pad fault'
  if n in ['base','even-junk']:assert bug['accepted'] is True and bug['pcmHex']==PCM
  check_wave(folder/'input.wav',o['wave'])
 return d
if __name__=='__main__':check(ROOT/(ROOT/'CURRENT').read_text().strip());print('PASS 7 hand byte/offset cases; strict/refusal and actual wave outcomes kept separate')
