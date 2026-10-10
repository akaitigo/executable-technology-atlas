# SPDX-License-Identifier: Apache-2.0
"""Actual classic mono PCM WAV bytes plus a finite packet-arrival toy. No codec/network stack."""
import io,struct,wave
VERSION='pcm-and-finite-jitter-1'


def validate_audio(a):
    if not isinstance(a,dict):raise ValueError('audio must be object')
    if a.get('format')!='pcm-s16le-mono':raise ValueError('only pcm-s16le-mono supported in this unit')
    rate=a.get('sample_rate');frames=a.get('chunk_frames');samples=a.get('samples')
    if type(rate) is not int or rate!=8000:raise ValueError('this fixture requires 8000Hz')
    if type(frames) is not int or not 1<=frames<=256:raise ValueError('chunk_frames must be integer 1..256')
    if not isinstance(samples,list) or not 1<=len(samples)<=4096:raise ValueError('samples requires 1..4096 integers')
    if any(type(x) is not int or not -32768<=x<=32767 for x in samples):raise ValueError('signed16 samples only; bool rejected')
    if len(samples)%frames or not 1<=len(samples)//frames<=16:raise ValueError('1..16 complete chunks required')
    if frames*1000%rate:raise ValueError('this toy uses integer millisecond cadence')
    return rate,frames,frames*1000//rate


def encode_wav(a):
    rate,frames,period=validate_audio(a);stream=io.BytesIO()
    with wave.open(stream,'wb') as out:
        out.setnchannels(1);out.setsampwidth(2);out.setframerate(rate)
        out.writeframes(struct.pack('<'+'h'*len(a['samples']),*a['samples']))
    return stream.getvalue()


def decode_wav(data):
    if not isinstance(data,bytes):raise ValueError('WAV input must be bytes')
    try:
        with wave.open(io.BytesIO(data),'rb') as source:
            channels,width,rate,frames,compression,_=source.getparams()
            if (channels,width,rate,compression)!=(1,2,8000,'NONE'):raise ValueError('only mono16 PCM 8000Hz supported here')
            pcm=source.readframes(frames)
            if len(pcm)!=frames*2:raise ValueError('truncated PCM data; readframes can return fewer frames')
            return dict(channels=channels,sample_width_bytes=width,sample_rate=rate,frames=frames,compression=compression,samples=list(struct.unpack('<'+'h'*frames,pcm)),pcm_hex=pcm.hex())
    except (wave.Error,EOFError) as error:raise ValueError('unsupported or malformed WAV: '+str(error)) from error


def packets(f,a):
    rate,frames,period=validate_audio(a);count=len(a['samples'])//frames
    if not isinstance(f,dict) or not isinstance(f.get('arrivals'),list):raise ValueError('fixture requires arrivals list')
    if len(f['arrivals'])>count:raise ValueError('at most one packet per source chunk')
    result=[];seen=set()
    for i,p in enumerate(f['arrivals']):
        if not isinstance(p,dict) or set(p)!={'seq','pts_ms','arrival_ms'}:raise ValueError('packet fields must be seq/pts_ms/arrival_ms')
        seq,pts,arrival=p['seq'],p['pts_ms'],p['arrival_ms']
        if type(seq) is not int or not 0<=seq<count or seq in seen:raise ValueError('seq outside source or duplicate')
        if type(pts) is not int or pts!=seq*period:raise ValueError('PTS must match source chunk cadence')
        if type(arrival) is not int or not pts<=arrival<=200:raise ValueError('arrival must be integer between PTS and 200ms')
        seen.add(seq);result.append(dict(**p,input_index=i,samples=a['samples'][seq*frames:(seq+1)*frames]))
    return sorted(result,key=lambda p:(p['arrival_ms'],p['input_index']))


def simulate(f,a,policy='pts',delay_ms=0):
    if policy not in ('pts','arrival-order'):raise ValueError('unknown buffer policy')
    if type(delay_ms) is not int or not 0<=delay_ms<=60:raise ValueError('startup delay must be integer 0..60ms')
    rate,frames,period=validate_audio(a);count=len(a['samples'])//frames;incoming=packets(f,a)
    cursor=0;buffer=[];trace=[];output=[];peak=0;late=[]
    for slot in range(count):
        now=delay_ms+slot*period;arrived=[];dropped=[]
        while cursor<len(incoming) and incoming[cursor]['arrival_ms']<=now:
            packet=incoming[cursor];cursor+=1;arrived.append(packet['seq'])
            if policy=='pts' and packet['seq']<slot:
                dropped.append(packet['seq']);late.append(packet['seq'])
            else:buffer.append(packet)
        before=[p['seq'] for p in buffer];peak=max(peak,len(buffer));chosen=None
        if policy=='pts':
            for i,packet in enumerate(buffer):
                if packet['seq']==slot:chosen=buffer.pop(i);break
        elif buffer:chosen=buffer.pop(0)  # Intentional naive arrival-order playout, ignoring PTS.
        samples=chosen['samples'] if chosen else [0]*frames;output.extend(samples)
        trace.append(dict(slot=slot,play_at_ms=now,expected_seq=slot,expected_pts_ms=slot*period,arrived=arrived,dropped_late=dropped,
                          buffer_before=before,played_seq=chosen['seq'] if chosen else None,buffer_after=[p['seq'] for p in buffer],
                          underflow=chosen is None,pts_mismatch=chosen is not None and chosen['seq']!=slot,
                          residence_ms=now-chosen['arrival_ms'] if chosen else None,output_samples=samples))
    underflows=sum(r['underflow'] for r in trace);mismatches=sum(r['pts_mismatch'] for r in trace)
    return dict(policy=policy,startup_delay_ms=delay_ms,cadence_ms=period,status='ORDERED' if underflows==mismatches==0 else 'IMPAIRED',
                underflows=underflows,pts_mismatches=mismatches,played=[r['played_seq'] for r in trace],output_samples=output,
                output_matches_source=output==a['samples'],buffer_peak_packets=peak,dropped_late=late,
                unplayed_buffer=[p['seq'] for p in buffer],future_packets=[p['seq'] for p in incoming[cursor:]],trace=trace,
                scope='Fixed relative-millisecond arrivals, finite slots, zero-fill gaps; no network, adaptive jitter estimator, compressed codec, PLC quality or actual playback timing')
