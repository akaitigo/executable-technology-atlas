import sqlite3
def process(path,f):
    db=sqlite3.connect(path)
    try:
        db.execute('CREATE TABLE message(seq INTEGER PRIMARY KEY, id TEXT UNIQUE, payload BLOB)')
        seed=f['seed'].encode('utf-8');db.execute('INSERT INTO message VALUES(0,?,?)',('old',seed));db.commit()
        start=db.total_changes;rows=[dict(id='old',payload_hex=seed.hex(),bytes=len(seed))];evicted=[];status='REJECTED';reason=None;accepted=False;payload=f['payload'];budget=f['budget'];policy=f['policy'];trace=['seed committed; mutation counter baseline recorded']
        if type(budget) is not int:status='INPUT_REJECTED';reason='BUDGET_TYPE'
        elif budget<0:status='INPUT_REJECTED';reason='BUDGET_RANGE'
        elif policy not in ['RejectNew','OverwriteOldest','CharCountFault']:status='INPUT_REJECTED';reason='POLICY'
        elif not isinstance(payload,str) or len(payload)>16:status='INPUT_REJECTED';reason='INPUT_SIZE'
        elif not payload:status='INPUT_REJECTED';reason='EMPTY_PAYLOAD'
        else:
            blob=payload.encode('utf-8')
            if len(blob)>budget:reason='SINGLE_PAYLOAD_EXCEEDS_BUDGET'
            else:
                cost=len(f['seed'])+len(payload) if policy=='CharCountFault' else len(seed)+len(blob)
                trace.append(dict(budget=budget,decision_cost=cost,actual_combined_bytes=len(seed)+len(blob)))
                if cost>budget and policy=='RejectNew':reason='FULL'
                else:
                    if cost>budget:
                        db.execute('DELETE FROM message WHERE id=?',('old',));rows=[];evicted=['old']
                    db.execute('INSERT INTO message VALUES(1,?,?)',('new',blob));db.commit();rows.append(dict(id='new',payload_hex=blob.hex(),bytes=len(blob)));accepted=True
                    status='EVICTED' if evicted else 'APPENDED'
                    if sum(x['bytes'] for x in rows)>budget:status='BAD_ACCEPTED'
        used=sum(x['bytes'] for x in rows)
        return dict(status=status,reason=reason,rows=rows,used_bytes=used,write_changes=db.total_changes-start,evicted=evicted,accepted=accepted,trace=trace,producer_connection_closed=True)
    finally:db.close()
