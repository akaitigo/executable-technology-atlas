def ai(rd,rs1,imm): return dict(op='ADDI',rd=rd,rs1=rs1,imm=imm)
def ad(rd,rs1,rs2): return dict(op='ADD',rd=rd,rs1=rs1,rs2=rs2)
def fixture(name,program,expected,none,cycles,initial=None):
    return dict(id=name,program=program,initial=initial or [0]*32,expected=expected,none=none,cycles=cycles)

FIXTURES = [
 fixture('chain',[ai(1,0,5),ad(2,1,1),ai(3,2,-1)],{1:5,2:10,3:9},{1:5,2:0,3:4294967295},[7,11,7]),
 fixture('independent',[ai(1,0,5),ai(2,0,7),ai(3,0,9)],{1:5,2:7,3:9},{1:5,2:7,3:9},[7,7,7]),
 fixture('priority',[ai(1,0,1),ai(1,1,1),ad(2,1,1)],{1:2,2:4},{1:1,2:0},[7,11,7]),
 fixture('two-source',[ai(1,0,3),ai(2,0,4),ad(3,1,2)],{1:3,2:4,3:7},{1:3,2:4,3:0},[7,9,7]),
 fixture('wb-gap',[ai(1,0,5),ai(4,0,1),ai(5,0,2),ad(2,1,1)],{1:5,2:10,4:1,5:2},{1:5,2:10,4:1,5:2},[8,8,8]),
 fixture('x0-write',[ai(0,0,9),ai(1,0,2)],{1:2},{1:2},[6,6,6]),
 fixture('imm-boundary',[ai(1,0,-2048),ai(2,0,2047),ad(3,1,2)],{1:4294965248,2:2047,3:4294967295},{1:4294965248,2:2047,3:0},[7,9,7]),
 fixture('wrap',[ai(2,1,1)],{1:4294967295,2:0},{1:4294967295,2:0},[5,5,5],[0,4294967295]+[0]*30),
 fixture('empty',[],{},{},[0,0,0]),
]

CHAIN_STAGES = [[1,None,None,None,None],[2,1,None,None,None],[3,2,1,None,None],
 [None,3,2,1,None],[None,None,3,2,1],[None,None,None,3,2],[None,None,None,None,3]]
CHAIN_STALL = [[1,None,None,None,None],[2,1,None,None,None],[3,2,1,None,None],
 [3,2,None,1,None],[3,2,None,None,1],[None,3,2,None,None],[None,3,None,2,None],
 [None,3,None,None,2],[None,None,3,None,None],[None,None,None,3,None],[None,None,None,None,3]]
