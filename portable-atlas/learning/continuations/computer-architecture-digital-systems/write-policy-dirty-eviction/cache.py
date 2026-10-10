# SPDX-License-Identifier: Apache-2.0
import copy
POLICIES=['write-through','write-back','broken-skip-dirty-eviction']
def validate(trace,policy):
    if policy not in POLICIES:raise ValueError('unknown policy')
    if not isinstance(trace,list) or len(trace)>64:raise ValueError('trace list length0..64 required')
    for op in trace:
        if not isinstance(op,dict) or op.get('op') not in ['load','store','flush']:raise ValueError('load/store/flush object required')
        expected={'op'} if op['op']=='flush' else {'op','address'} if op['op']=='load' else {'op','address','value'}
        if set(op)!=expected:raise ValueError('exact operation fields required')
        for key in expected-{'op'}:
            if type(op[key]) is not int or not 0<=op[key]<=255:raise ValueError(key+' exact integer0..255 required')
def initial():return [(17*a+3)%256 for a in range(256)]
class State:
    def __init__(self):self.memory=initial();self.line=None;self.data=[];self.dirty=False;self.transactions=0;self.bytes=0;self.writebacks=0
    def snapshot(self):return dict(valid=self.line is not None,block_address=self.line,cache_bytes=self.data[:],dirty=self.dirty,memory=self.memory[:],memory_write_transactions=self.transactions,memory_written_bytes=self.bytes,writebacks=self.writebacks)
class Through(State):
    def step(self,op):
        victim=None;events=[];ret=None;hit=None
        if op['op']=='flush':events.append('flush clean/no-op')
        else:
            address=op['address'];base=address-address%4;hit=self.line==base
            if not hit:
                victim=self.line;self.line=base;self.data=self.memory[base:base+4];events.append('write-allocate fill' if op['op']=='store' else 'load fill')
            if op['op']=='store':
                self.data[address%4]=op['value'];self.memory[address]=op['value'];self.transactions+=1;self.bytes+=1;events.append('write-through byte to memory')
            else:ret=self.data[address%4]
        return dict(return_byte=ret,hit=hit,victim_block_address=victim,events=events)
class Back(State):
    def __init__(self,broken=False):super().__init__();self.broken=broken
    def write_dirty(self,events):
        self.memory[self.line:self.line+4]=self.data[:];self.transactions+=1;self.bytes+=4;self.writebacks+=1;self.dirty=False;events.append('write-back victim/current block4bytes')
    def step(self,op):
        victim=None;events=[];ret=None;hit=None
        if op['op']=='flush':
            if self.dirty:self.write_dirty(events)
            else:events.append('flush clean/no-op')
        else:
            address=op['address'];base=(address//4)*4;hit=self.line==base
            if not hit:
                victim=self.line
                if self.dirty:
                    if self.broken:events.append('BUG: dirty victim write-back omitted')
                    else:self.write_dirty(events)
                self.line=base;self.data=list(self.memory[base:base+4]);self.dirty=False;events.append('write-allocate fill' if op['op']=='store' else 'load fill')
            if op['op']=='store':self.data[address-base]=op['value'];self.dirty=True;events.append('cache byte updated; dirty=true')
            else:ret=self.data[address-base]
        return dict(return_byte=ret,hit=hit,victim_block_address=victim,events=events)
def execute(trace,policy):
    validate(trace,policy);state=Through() if policy=='write-through' else Back(policy.startswith('broken'));rows=[]
    for index,op in enumerate(trace):
        before=state.snapshot();event=state.step(op);after=state.snapshot();rows.append(dict(step=index,input=copy.deepcopy(op),before=before,after=after,**event))
    return dict(policy=policy,geometry=dict(capacity_bytes=4,line_bytes=4,lines=1,write_allocate=True,memory_bytes=256),trace=rows,final=state.snapshot())
