#!/usr/bin/env python3
import json,pathlib,sqlite3,sys
SQL='SELECT id, display_name FROM person ORDER BY id'
def main():
    db=pathlib.Path(sys.argv[1]).resolve();con=sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True);con.execute('PRAGMA query_only=ON')
    try:
        rows=[list(r) for r in con.execute(SQL)];print(json.dumps({'version':'v2','sql':SQL,'rows':rows}));return 0
    except sqlite3.Error as e:
        print(json.dumps({'version':'v2','sql':SQL,'error':str(e),'errorClass':type(e).__name__,'sqliteErrorCode':getattr(e,'sqlite_errorcode',None),'sqliteErrorName':getattr(e,'sqlite_errorname',None)}));return 3
    finally:con.close()
if __name__=='__main__':sys.exit(main())
