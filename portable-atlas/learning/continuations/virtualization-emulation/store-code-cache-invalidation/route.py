import json,sys
sys.dont_write_bytecode=True
ROUTES={'self-modifying operand':'operand','opcode patch':'opcode','code外STORE':'data','無関係block':'unrelated','block末尾境界':'boundary','PC255 operand0':'wrap','入力/illegal/budget':'input,illegal,budget,last-halt'}
EXCLUDED=['native JIT','QEMU execution','VM boot','hypervisor isolation']
if __name__=='__main__':print(json.dumps({'routes':ROUTES,'excluded':EXCLUDED,'status':'finite-unit-only'},ensure_ascii=False))
