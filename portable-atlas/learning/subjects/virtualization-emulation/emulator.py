"""Toy ISA interpreter. All variants have a bounded execution budget."""
import hashlib
OPCODES={0x10:'LOAD',0x20:'ADD',0x30:'JZ',0xff:'HALT'}
def validate(spec):
 if type(spec) is not dict or set(spec)!={'program','pc','a','budget'}:raise ValueError('program/pc/a/budgetだけを持つobjectが必要')
 if type(spec['program']) is not list or not 1<=len(spec['program'])<=256:raise ValueError('programは1..256byteのlist')
 if any(type(b) is not int or not 0<=b<=255 for b in spec['program']):raise ValueError('program byteはinteger0..255（bool/float不可）')
 for k in ('pc','a'):
  if type(spec[k]) is not int or not 0<=spec[k]<=255:raise ValueError(k+'はinteger0..255')
 if type(spec['budget']) is not int or not 1<=spec['budget']<=64:raise ValueError('budgetはinteger1..64（bool/float不可）')
 return spec

def execute(spec,variant='correct'):
 if variant not in ('correct','naive-unbounded'):raise ValueError('未対応variant')
 validate(spec)
 memory=bytes(spec['program']+[0]*(256-len(spec['program'])))
 pc,a=spec['pc'],spec['a'];trace=[];fault=None;halted=False
 for step in range(spec['budget']):
  if not 0<=pc<256:fault={'reason':'pc_oob','pc':pc};break
  opcode=memory[pc]
  if opcode not in OPCODES:fault={'reason':'illegal_opcode','pc':pc,'opcode':opcode};break
  op=OPCODES[opcode];before={'pc':pc,'a':a};operand=None;operand_addr=None;taken=None
  if op!='HALT':
   operand_addr=(pc+1)&255 if variant=='correct' else pc+1
   if not 0<=operand_addr<256:fault={'reason':'operand_oob','pc':pc,'operand_address':operand_addr};break
   operand=memory[operand_addr]
   next_pc=(pc+2)&255 if variant=='correct' else pc+2
   if op=='LOAD':a=operand;pc=next_pc
   elif op=='ADD':a=((a+operand)&255) if variant=='correct' else a+operand;pc=next_pc
   elif op=='JZ':taken=a==0;pc=operand if taken else next_pc
  else:halted=True
  trace.append({'step':step,'before':before,'opcode_address':before['pc'],'opcode':opcode,'operand_address':operand_addr,'operand':operand,'op':op,'taken':taken,'after':{'pc':pc,'a':a},'halted':halted})
  if halted:break
 if not halted and fault is None:fault={'reason':'step_budget','budget':spec['budget'],'pc':pc}
 return {'status':'halted' if halted else 'rejected','state':{'pc':pc,'a':a},'steps':len(trace),'trace':trace,'fault':fault,'memory_sha256':hashlib.sha256(memory).hexdigest()}

def analyze(spec):
 try:validate(spec)
 except ValueError as e:return {'status':'rejected','phase':'input','error':str(e),'variants':{}}
 variants={v:execute(spec,v) for v in ('correct','naive-unbounded')}
 memory=spec['program']+[0]*(256-len(spec['program']))
 return {'status':'accepted' if variants['correct']['status']=='halted' else 'rejected','phase':'execution','input':spec,'memory':memory,'loaded_bytes':len(spec['program']),'variants':variants,'note':'naive-unbounded refers to register/PC width; both variants use the same finite step budget'}
