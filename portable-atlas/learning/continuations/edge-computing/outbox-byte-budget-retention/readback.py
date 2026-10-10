import sqlite3
def read(path):
    db=sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True)
    try:
        rows=[dict(id=i,payload_hex=h.lower(),bytes=n) for i,h,n in db.execute('SELECT id,hex(payload),length(payload) FROM message ORDER BY seq')]
        return dict(rows=rows,used_bytes=sum(x['bytes'] for x in rows),readonly=True,reopened_after_producer_close=True)
    finally:db.close()
