"""Independent list-reader/index oracle; no import from producer or its helpers."""
import csv
from io import StringIO


def oracle(data):
    source=csv.reader(StringIO(data["csv"],newline=""),strict=True)
    parsed=[]; ends=[]
    try:
        for cells in source: parsed.append(cells);ends.append(source.line_num)
    except csv.Error:return {"category":"rejected","reason":"csv_syntax","typed_rows":[]}
    reason=None
    if not 2<=len(parsed)<=5 or any(not row or len(row)>5 for row in parsed):
        reason="record_bounds"
    header=parsed[0] if parsed else []
    if reason is None:
        if len(header)!=len(set(header)):reason="duplicate_header"
        elif "" in header:reason="empty_header"
        elif not all(f in header for f in ("id","quantity","unit_price")):reason="required_header"
        elif any(f not in (("id","quantity","unit_price") if data["reader"]=="v1" else
                          ("id","quantity","unit_price","note")) for f in header):reason="unknown_header"
    rows=[]
    for cells in parsed[1:] if reason is None else []:
        if len(cells)>len(header):reason="extra_cells";break
        if len(cells)<len(header):reason="missing_cells";break
        fields=["id","quantity","unit_price"]+(["note"] if data["reader"]=="v2" else [])
        typed={}
        for i,field in enumerate(fields):
            index=header.index(field) if field in header else None
            if data["mode"]=="position-fault" and index is not None:index=i
            v=cells[index] if index is not None else "(default)"
            if field=="id":
                if not 1<=len(v)<=8 or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_" for c in v):
                    reason="id_lexeme";break
                typed[field]=v
            elif field in ("quantity","unit_price"):
                if not v or len(v)>2 or any(c not in "0123456789" for c in v) or (len(v)>1 and v[0]=="0"):
                    reason="integer_lexeme";break
                typed[field]=int(v)
            else:
                if len(v)>16 or any(ord(c)>127 for c in v):reason="note_lexeme";break
                typed[field]=v
        if reason:break
        rows.append(typed)
    return {"category":"rejected" if reason else "accepted","reason":reason,
            "typed_rows":[] if reason else rows}
