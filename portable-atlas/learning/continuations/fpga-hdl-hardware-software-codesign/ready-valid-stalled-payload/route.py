import json,sys
sys.dont_write_bytecode=True
print(json.dumps({'routes':{'stall':'stall17,retired,wrap','即ready':'ready-first,zero','未transfer':'never-ready,not-valid,empty','入力拒否':'bool-ready,bool-data,bad-ready,long,float-data,extra,malformed'},'refuse':['RTL success','FPGA timing','CDC safety','AXI certification'],'scope':'finite-only'},ensure_ascii=False))
