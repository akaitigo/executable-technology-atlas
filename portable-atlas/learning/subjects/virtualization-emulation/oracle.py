"""Independent successor/addition table interpreter, no emulator import or masking."""
SUCCESSOR=tuple(range(1,256))+(0,)
ADVANCE_TWO=tuple(SUCCESSOR[SUCCESSOR[p]] for p in range(256))
rows=[]
for base in range(256):
 row=[base]
 for _ in range(255):row.append(SUCCESSOR[row[-1]])
 rows.append(tuple(row))
ADD_TABLE=tuple(rows)
NAMES={16:'LOAD',32:'ADD',48:'JZ',255:'HALT'}
def expected(spec):
 memory=spec['program']+[0]*(256-len(spec['program']))
 state=(spec['pc'],spec['a']);trace=[]
 for number in range(spec['budget']):
  pc,a=state;opcode=memory[pc]
  if opcode not in NAMES:return {'status':'rejected','state':{'pc':pc,'a':a},'steps':len(trace),'trace':trace,'fault':{'reason':'illegal_opcode','pc':pc,'opcode':opcode}}
  name=NAMES[opcode];addr=None;imm=None;taken=None;halt=name=='HALT'
  after=state
  if not halt:
   addr=SUCCESSOR[pc];imm=memory[addr]
   if name=='LOAD':after=(ADVANCE_TWO[pc],imm)
   if name=='ADD':after=(ADVANCE_TWO[pc],ADD_TABLE[a][imm])
   if name=='JZ':taken=a==0;after=(imm if taken else ADVANCE_TWO[pc],a)
  trace.append({'step':number,'before':{'pc':pc,'a':a},'opcode_address':pc,'opcode':opcode,'operand_address':addr,'operand':imm,'op':name,'taken':taken,'after':{'pc':after[0],'a':after[1]},'halted':halt})
  state=after
  if halt:return {'status':'halted','state':trace[-1]['after'],'steps':len(trace),'trace':trace,'fault':None}
 return {'status':'rejected','state':{'pc':state[0],'a':state[1]},'steps':len(trace),'trace':trace,'fault':{'reason':'step_budget','budget':spec['budget'],'pc':state[0]}}
