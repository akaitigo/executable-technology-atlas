import json,sys
sys.dont_write_bytecode=True
print(json.dumps({'routes':{'stale writer昇格':'stale,stale-small','snapshot取得時点':'fresh,fresh-high','writer取消':'rollback,rollback-high','BUSYの区別':'busy,busy-zero','API欠測':'qa/toolchain.json'},'refuse':['user path/SQL','existing DB','all BUSY classification','timeout guarantees','crash recovery'],'scope':'third finite unit acceptance pending'},ensure_ascii=False))
