import csv
import hashlib
from io import StringIO
import json
import re
import sys

REQUIRED=["id","quantity","unit_price"]


def write(version):
    fields=REQUIRED+(["note"] if version=="v2" else [])
    row={"id":"a","quantity":2,"unit_price":7}
    if version=="v2": row["note"]="batch"
    stream=StringIO(newline="")
    writer=csv.DictWriter(stream,fieldnames=fields,extrasaction="raise",lineterminator="\n")
    writer.writeheader(); writer.writerow(row)
    return stream.getvalue()


def calculate(d):
    if (not isinstance(d,dict) or set(d)!={"writer","reader","mode","csv"}
        or d["writer"] not in ("literal","v1","v2") or d["reader"] not in ("v1","v2")
        or d["mode"] not in ("name","position-fault") or not isinstance(d["csv"],str)
        or len(d["csv"].encode("utf-8"))>1024):
        return {"category":"input_refused","error":"exact bounded writer,reader,mode,csv required"}
    raw=d["csv"]
    writer_output=write(d["writer"]) if d["writer"]!="literal" else None
    if writer_output is not None and writer_output!=raw:
        return {"category":"input_refused","error":"actual writer bytes differ from supplied csv"}
    result={"category":"rejected","reason":None,"typed_rows":[],"header":[],
            "mapping":[],"records":[],"csv":raw,"csv_sha256":hashlib.sha256(raw.encode()).hexdigest(),
            "writer_output":writer_output,"runtime":sys.version.split()[0],"reader":d["reader"],"mode":d["mode"]}

    def refuse(reason,record=0,field=None,end_line=1):
        result.update(reason=reason,error_at={"record":record,"field":field,"end_line":end_line})
        return result

    try:
        scanner=csv.reader(StringIO(raw,newline=""),strict=True)
        physical=[]
        for values in scanner: physical.append((values,scanner.line_num))
        if not 2<=len(physical)<=5 or any(not cells or len(cells)>5 for cells,_ in physical):
            return refuse("record_bounds")
        reader=csv.DictReader(StringIO(raw,newline=""),restkey="__extra__",restval=None,strict=True)
        header=reader.fieldnames or []
        result["header"]=header
        if len(set(header))!=len(header):return refuse("duplicate_header")
        if any(not name for name in header):return refuse("empty_header")
        if not set(REQUIRED)<=set(header):return refuse("required_header")
        allowed=REQUIRED+(["note"] if d["reader"]=="v2" else [])
        if set(header)-set(allowed):return refuse("unknown_header")
        for field in allowed:
            position=(header.index(field) if field in header else None) if d["mode"]=="name" else (
                      allowed.index(field) if field in header else None)
            result["mapping"].append({"field":field,"column":position+1 if position is not None else None,
                                      "default":"(default)" if field=="note" and field not in header else None})
        typed=[]
        for ordinal,row in enumerate(reader,1):
            values=physical[ordinal][0]
            end_line=reader.line_num
            entry={"record":ordinal,"end_line":end_line,"cells":values,"mapped":{}}
            result["records"].append(entry)
            if "__extra__" in row:return refuse("extra_cells",ordinal,None,end_line)
            if any(v is None for v in row.values()):return refuse("missing_cells",ordinal,None,end_line)
            target={}
            for mapping in result["mapping"]:
                field=mapping["field"]
                value=(row[field] if d["mode"]=="name" else values[mapping["column"]-1]) if mapping["column"] is not None else mapping["default"]
                entry["mapped"][field]=value
                if field=="id":
                    if not re.fullmatch(r"[A-Za-z0-9_]{1,8}",value):return refuse("id_lexeme",ordinal,field,end_line)
                    target[field]=value
                elif field in ("quantity","unit_price"):
                    if not re.fullmatch(r"(0|[1-9][0-9]?)",value):return refuse("integer_lexeme",ordinal,field,end_line)
                    target[field]=int(value)
                else:
                    if len(value)>16 or not value.isascii():return refuse("note_lexeme",ordinal,field,end_line)
                    target[field]=value
            entry["typed"]=target; typed.append(target)
        result.update(category="accepted",typed_rows=typed,error_at=None)
        return result
    except csv.Error:
        return refuse("csv_syntax",end_line=scanner.line_num)


if __name__=="__main__":
    try: out=calculate(json.loads(sys.stdin.read()))
    except (ValueError,TypeError,UnicodeError):out={"category":"input_refused","error":"invalid JSON"}
    print(json.dumps(out,ensure_ascii=False,sort_keys=True))
