"""Atlas: read-only resource observation for one tiny owned file experiment."""
import json, os, re, subprocess
from datetime import datetime, timezone
from pathlib import Path

result = {"observed_at": datetime.now(timezone.utc).isoformat(), "cpu_count": os.cpu_count(), "load": list(os.getloadavg()), "reads": {}, "blockers": [], "native_executions": 0, "browser_started": False}
def read(label, args):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=8)
        result["reads"][label] = {"exit_code": p.returncode, "stderr": p.stderr.strip()}
        if p.returncode:
            result["blockers"].append(label + " unavailable; not zero")
            return ""
        return p.stdout
    except Exception as e:
        result["blockers"].append(label + ": " + type(e).__name__)
        return ""
cpu = read("cpu", ["/usr/bin/top", "-l", "2", "-s", "1", "-n", "0"])
pressure = read("memory-pressure", ["/usr/bin/memory_pressure", "-Q"])
vm = read("vm", ["/usr/bin/vm_stat"])
processes = read("processes", ["/bin/ps", "-axo", "pid=,pcpu=,rss=,comm="])
try:
    samples = re.findall(r"CPU usage: ([\d.]+)% user, ([\d.]+)% sys, ([\d.]+)% idle", cpu)
    result["cpu_samples"] = [{"user":float(u),"system":float(s),"idle":float(i)} for u,s,i in samples]
    if len(samples)<2 or result["cpu_samples"][-1]["idle"]<30: result["blockers"].append("CPU samples unavailable or aggregate idle below 30%")
    free = re.search(r"System-wide memory free percentage:\s*(\d+)%", pressure)
    result["memory_free_percent"] = int(free[1]) if free else None
    page = re.search(r"page size of (\d+) bytes", vm)
    amount = sum(int(re.search(r"Pages " + label + r":\s+(\d+)", vm)[1]) for label in ["free","speculative","inactive"]) * int(page[1]) if page else None
    result["available_memory_estimate_bytes"] = amount
    if not free or int(free[1])<15 or amount is None or amount<2*1024**3: result["blockers"].append("memory observation insufficient or below headroom limit")
    rows=[]
    for line in processes.splitlines():
        pid,cpu_pct,rss,command=line.strip().split(None,3)
        rows.append({"pid":int(pid),"cpu_percent":float(cpu_pct),"rss_kib":int(rss),"name":Path(command).name,"playwright_cache": "ms-playwright" in command})
    result["process_count"] = len(rows) if processes else None
    result["existing_headless_browser"] = [r for r in rows if r["playwright_cache"] or "headless" in r["name"].lower()] if processes else None
    watched={"wrk","wrk2","hey","sysbench","stress","stress-ng","iperf3","k6","vegeta","kotlinc","rustc","clang","clang++","flutter","dart"}
    result["known_heavy_processes"] = [r for r in rows if r["name"].lower() in watched] if processes else None
    result["top_cpu_diagnostics"] = sorted(rows,key=lambda r:r["cpu_percent"],reverse=True)[:5]
    # Root owns a browser slot; this tiny OS experiment does not use it.
    result["browser_note"] = "Existing browser is recorded, not changed or treated alone as an OS experiment blocker."
    if result["known_heavy_processes"]: result["blockers"].append("known compiler or benchmark present")
    if not result["cpu_count"] or result["load"][0]/result["cpu_count"]>.75: result["blockers"].append("one-minute load per logical CPU exceeds .75")
except Exception as e:
    result["blockers"].append("unparsed observation: "+type(e).__name__)
result["allowed"]=not result["blockers"]
result["limits"]={"minimum_idle_percent":30,"maximum_load_per_cpu":.75,"minimum_memory_free_percent":15,"minimum_available_memory_estimate_bytes":2*1024**3}
result["limitations"]="Instantaneous observations, memory estimate not guaranteed allocatable; name search cannot prove absence of unknown processes. No other process or OS setting changed."
print(json.dumps(result,indent=2))
