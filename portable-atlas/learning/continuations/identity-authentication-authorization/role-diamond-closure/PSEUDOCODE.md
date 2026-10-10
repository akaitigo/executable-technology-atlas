# Atlas：固定した訪問手順

edge順はinputs/cases.jsonの配列順です。permission結果の辞書順整形とDFS順を混ぜません。visitedとcompletedは順序付き集合相当、activeは現在経路です。

```text
visited=[], active=[], completed=[], events=[]
emit START(requested_role)
if requested_role not in graph:
    emit REJECT_UNKNOWN; return rejection(all permission/closure fields null)

visit(role):
    if normal and role in active:
        cycle_path = suffix(active, first role occurrence) + [role]
        emit REJECT_CYCLE; return false
    if fault and role in visited:
        reported_path = active + [role]  # cycleとは限らない
        emit REJECT_REVISIT; return false
    if role in visited:
        emit REUSE; return true
    visited.append(role); active.append(role)
    emit ENTER
    for inherited in graph[role]:
        emit EDGE(role, target=inherited)
        if not visit(inherited): return false  # 次のedgeへ進まない
    active.pop(); completed.append(role)
    emit LEAVE
    return true

if visit(requested_role):
    reachable_order = copy(visited); reachable_set = sorted(visited)
    direct = set(grants[requested_role])
    inherited = union grants[r] for r in visited if r != requested_role
    effective = direct union inherited; overlap = direct intersection inherited
    sources[p] = sorted(distinct r in visited with p in grants[r])
    emit ACCEPT; return accepted(sorted sets and sources)
else:
    return rejected(all closure/permission result fields null,
                    diagnostic copy of visited/completed/active and rejection path)
```

emitはindex（0から）/action/role/target/active/visited_order/completed_order/cycle_path/reported_pathをcopyする。通常のpath2項はnull、拒否位置だけ対応するpathが入ります。STARTとACCEPTのroleは要求role、targetはnull。EDGEだけtargetがあり、他actionのroleはその訪問role。ACCEPTは全LEAVE後、拒否の後にACCEPTを出しません。permission計算は成功した後だけです。
