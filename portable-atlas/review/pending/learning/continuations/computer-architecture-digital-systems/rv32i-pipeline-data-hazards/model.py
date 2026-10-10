"""Finite educational pipeline, not a machine-code decoder."""
from copy import deepcopy

MOD = 2**32
MODES = ('none', 'stall', 'forwarding')

def integer(v, lo, hi):
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError('integer outside finite contract')

def validate(program, initial, mode):
    if mode not in MODES or type(mode) is not str:
        raise ValueError('unknown mode')
    if type(program) is not list or len(program) > 12:
        raise ValueError('program must contain 0..12 instructions')
    if type(initial) is not list or len(initial) != 32:
        raise ValueError('32 initial registers required')
    for v in initial:
        integer(v, 0, MOD-1)
    if initial[0] != 0:
        raise ValueError('x0 must be zero')
    for ins in program:
        if type(ins) is not dict or ins.get('op') not in ('ADD','ADDI'):
            raise ValueError('only ADD and ADDI')
        keys = {'op','rd','rs1','rs2'} if ins['op']=='ADD' else {'op','rd','rs1','imm'}
        if set(ins) != keys:
            raise ValueError('exact instruction fields required')
        for key in keys & {'rd','rs1','rs2'}:
            integer(ins[key], 0, 31)
        if ins['op']=='ADDI':
            integer(ins['imm'], -2048, 2047)

def sources(ins):
    return [ins['rs1'], ins['rs2']] if ins['op']=='ADD' else [ins['rs1']]

def run(program, initial, mode, mutant=None):
    validate(program, initial, mode)
    regs = initial[:]
    pipe = [dict(i=0, ins=program[0])] + [None]*4 if program else [None]*5
    fetched = 1 if program else 0
    trace, retired = [], 0
    stalls = 0
    while any(p is not None for p in pipe):
        assert len(trace) < 80, 'finite drain bound'
        f,d,e,m,w = pipe
        before = regs[:]
        if w and (w['ins']['rd'] != 0 or mutant=='write_x0'):
            regs[w['ins']['rd']] = w['result']
        if w:
            retired += 1
        result, operands, paths = None, [], []
        if e:
            for k,s in enumerate(sources(e['ins'])):
                value, path = e['operands'][k], 'ID-latch'
                if s==0 and mutant!='forward_x0':
                    value,path = 0,'x0'
                elif mode=='forwarding':
                    candidates = [('MEM',m),('WB',w)]
                    if mutant=='old_priority':
                        candidates.reverse()
                    if mutant=='drop_wb':
                        candidates = [('MEM',m)]
                    for label,p in candidates:
                        if p and p['ins']['rd']==s and (s!=0 or mutant=='forward_x0'):
                            value,path = p['result'],label
                            break
                operands.append(value); paths.append(path)
            b = operands[1] if e['ins']['op']=='ADD' else e['ins']['imm']
            if mutant=='unsigned_imm' and e['ins']['op']=='ADDI':
                b %= 4096
            result = operands[0]+b
            if mutant!='no_wrap':
                result %= MOD
        pending = []
        if d:
            for s in sources(d['ins']):
                producers = [('EX',e),('MEM',m)]
                if mutant=='ignore_mem_stall':
                    producers = [('EX',e)]
                for label,p in producers:
                    if s!=0 and p and p['ins']['rd']==s:
                        pending.append(dict(source=s,producer=p['i']+1,stage=label))
        wait = mode=='stall' and bool(pending)
        if wait:
            stalls += 1
        next_e = None
        if d and not wait:
            read_regs = before if mutant=='read_before_wb' else regs
            next_e = dict(d, operands=[read_regs[s] for s in sources(d['ins'])])
        next_f = f if wait else (dict(i=fetched,ins=program[fetched]) if fetched<len(program) else None)
        if not wait and fetched<len(program):
            fetched += 1
        next_m = dict(e,result=result) if e else None
        trace.append(dict(cycle=len(trace)+1,stages=[p['i']+1 if p else None for p in pipe],
                          stalled=wait,pending=pending,ex_operands=operands,ex_paths=paths,
                          ex_result=result,wb=w['i']+1 if w else None,registers=regs[:]))
        pipe = [next_f,d if wait else f,next_e,next_m,m]
    return dict(mode=mode,cycles=len(trace),stalls=stalls,retired=retired,registers=regs,trace=trace)
