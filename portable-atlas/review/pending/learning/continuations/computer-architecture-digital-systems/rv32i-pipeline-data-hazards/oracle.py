"""Instruction-order oracle, independent of pipeline execution and helper functions."""
def sequential(program, initial):
    bank = dict(enumerate(initial))
    for inst in program:
        left = 0 if inst['rs1']==0 else bank[inst['rs1']]
        right = inst['imm'] if inst['op']=='ADDI' else (0 if inst['rs2']==0 else bank[inst['rs2']])
        total = (left + right) & 0xffffffff
        if inst['rd']:
            bank[inst['rd']] = total
    return [bank[i] for i in range(32)]
