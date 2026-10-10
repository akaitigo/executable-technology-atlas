# SPDX-License-Identifier: Apache-2.0
"""Finite ideal-timed BPSK complex baseband. No RF, SDR device or standard modem."""
import math
VERSION='finite-bpsk-pilot-1'
ROTATIONS={0:complex(1,0),90:complex(0,1),180:complex(-1,0),270:complex(0,-1)}


def validate(base,f):
    if not isinstance(base,dict) or not isinstance(f,dict):raise ValueError('base/fixture must be objects')
    for name,lower,upper in [('bits',1,128),('pilot_bits',2,16)]:
        bits=base.get(name)
        if not isinstance(bits,list) or not lower<=len(bits)<=upper or any(type(v) is not int or v not in (0,1) for v in bits):raise ValueError(name+' must contain finite integer0/1 bits; bool rejected')
    sps=base.get('samples_per_symbol');rate=base.get('symbol_rate')
    if type(sps) is not int or not 1<=sps<=16:raise ValueError('samples_per_symbol must be integer1..16')
    if type(rate) is not int or not 1<=rate<=10000:raise ValueError('symbol_rate must be integer1..10000')
    phase=f.get('phase_deg');gain=f.get('gain')
    if type(phase) is not int or phase not in ROTATIONS:raise ValueError('this unit supports exact quadrant phases0/90/180/270 only')
    if type(gain) not in (int,float) or not math.isfinite(gain) or not 0<=gain<=2:raise ValueError('gain must be finite0..2; bool rejected')
    for name,n in [('noise',len(base['bits'])),('pilot_noise',len(base['pilot_bits']))]:
        noise=f.get(name)
        if not isinstance(noise,list) or len(noise)!=n:raise ValueError(name+' length must match symbols')
        for pair in noise:
            if not isinstance(pair,list) or len(pair)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) or not -4<=v<=4 for v in pair):raise ValueError('noise needs finite I/Q pairs -4..4')
    return sps,rate


def modulate(bits,sps):return [complex(1 if bit==0 else -1,0) for bit in bits for _ in range(sps)]
def average(samples,sps):return [sum(samples[i:i+sps])/sps for i in range(0,len(samples),sps)]
def pairs(samples):return [[v.real,v.imag] for v in samples] if samples is not None else None


def execute(base,f,mode='pilot'):
    if mode not in ('none','pilot'):raise ValueError('unknown phase correction mode')
    sps,rate=validate(base,f);channel=f['gain']*ROTATIONS[f['phase_deg']]
    tx=modulate(base['bits'],sps);pilot_tx=modulate(base['pilot_bits'],sps)
    rx=[v*channel+complex(*f['noise'][i//sps]) for i,v in enumerate(tx)]
    pilot_rx=[v*channel+complex(*f['pilot_noise'][i//sps]) for i,v in enumerate(pilot_tx)]
    received_symbols=average(rx,sps);pilot_symbols=average(pilot_rx,sps)
    estimate=sum(v*(1 if bit==0 else -1) for v,bit in zip(pilot_symbols,base['pilot_bits']))/len(pilot_symbols)
    available=estimate!=0
    factor=(estimate.conjugate()/abs(estimate) if available else None) if mode=='pilot' else complex(1,0)
    decision_samples=[v*factor for v in rx] if factor is not None else None
    decisions=average(decision_samples,sps) if decision_samples is not None else None
    decoded=[1 if v.real<0 else 0 for v in decisions] if decisions is not None else None
    errors=[i for i,bit in enumerate(decoded) if bit!=base['bits'][i]] if decoded is not None else None
    trace=[]
    for i,bit in enumerate(base['bits']):
        trace.append(dict(index=i,input_bit=bit,tx_symbol=[1 if bit==0 else -1,0],received_symbol=pairs([received_symbols[i]])[0],
                          decision_symbol=pairs([decisions[i]])[0] if decisions is not None else None,decoded_bit=decoded[i] if decoded is not None else None,
                          hard_tie=decisions[i].real==0 if decisions is not None else None,incorrect=(i in errors) if errors is not None else None,
                          sample_range=[i*sps,(i+1)*sps],decision_rule='I<0 ->bit1; I>=0 including exact tie ->bit0'))
    return dict(status='NO_PHASE_ESTIMATE' if decoded is None else ('MATCH' if not errors else 'BIT_ERRORS'),mode=mode,
                decoded_bits=decoded,error_indices=errors,error_count=len(errors) if errors is not None else None,
                compared_bits=len(base['bits']) if decoded is not None else 0,ber=len(errors)/len(base['bits']) if errors is not None else None,
                pilot_estimate=[estimate.real,estimate.imag],estimated_phase_deg=math.degrees(math.atan2(estimate.imag,estimate.real)) if available else None,
                correction_factor=[factor.real,factor.imag] if factor is not None else None,pilot_phase_available=available,
                samples_per_symbol=sps,symbol_rate=rate,sample_rate=rate*sps,payload_sample_count=len(tx),payload_duration_ms=len(base['bits'])*1000/rate,
                transmit_samples=pairs(tx),received_samples=pairs(rx),decision_samples=pairs(decision_samples),received_symbols=pairs(received_symbols),decision_symbols=pairs(decisions),
                pilot_transmit_samples=pairs(pilot_tx),pilot_received_samples=pairs(pilot_rx),pilot_received_symbols=pairs(pilot_symbols),trace=trace,
                scope='Calculated ideal-timed complex baseband, rectangular pulse and symbol-held fixed noise. No RF/SDR/standard conformance, AWGN BER curve or real synchronization.')
