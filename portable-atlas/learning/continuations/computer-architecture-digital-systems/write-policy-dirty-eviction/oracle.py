# SPDX-License-Identifier: Apache-2.0
"""Sequential byte-memory specification; imports no cache producer, has no cache replacement logic."""
def initial_memory():
    result=[];v=3
    for address in range(256):result.append(v);v=(v+17)%256
    return result
def sequential(trace):
    memory=initial_memory();steps=[]
    for op in trace:
        returned=None
        if op['op']=='store':memory[op['address']]=op['value']
        elif op['op']=='load':returned=memory[op['address']]
        steps.append(dict(expected_return_byte=returned,logical_memory=memory[:]))
    return steps
