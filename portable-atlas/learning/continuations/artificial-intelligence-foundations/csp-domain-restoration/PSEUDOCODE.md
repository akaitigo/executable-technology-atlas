# Atlas：探索の順序とdomain復元の疑似コード

これは実装前に固定した手順です。domainの格納は集合でよいですが、表示・候補・neighbor走査は固定順です。modeはbaseline / forward-checking / missing-restore。trailは削除した(variable,color)の順序付き列です。

```text
search(depth):
  search_calls += 1
  record ENTER (assignment, domains, trail)
  if depth == 4:
    append COPY(assignment) to solutions
    solutions_count += 1
    record SOLUTION
    return

  v = variables[depth]
  candidates = sorted COPY(domains[v])    # 入側で一度だけ
  record CANDIDATES(v, candidates)
  for color in candidates:
    candidate_attempts += 1
    record TRY(v,color)
    ok = true
    for n in sorted neighbors[v]:
      if n is assigned:
        assigned_constraint_tests += 1
        record CHECK_ASSIGNED(v,color,n,assignment[n], color != assignment[n])
        if color == assignment[n]:
          consistency_rejections += 1
          ok = false
          break
    if not ok:
      record REJECT_CANDIDATE
      continue

    mark = len(trail)
    assignment[v] = color
    record ASSIGN
    viable = true
    if mode != baseline:
      for n in sorted neighbors[v]:
        if n is unassigned:
          for candidate in sorted COPY(domains[n]):
            propagation_tests += 1
            record CHECK_FUTURE(v,color,n,candidate,color != candidate)
            if color == candidate:
              remove candidate from domains[n]
              append (n,candidate) to trail
              removed_values += 1
              record PRUNE (reason: v=color and v != n)
          if domains[n] is empty:
            domain_wipeouts += 1
            record WIPEOUT(n)        # 後続neighborを走査しない
            viable = false
            break
    if viable:
      search(depth + 1)

    if mode == forward-checking:
      while len(trail) > mark:
        n,candidate = trail.pop()
        insert candidate into domains[n]
        restored_values += 1
        record RESTORE(n,candidate)
    if mode == missing-restore:
      record RESTORE_OMITTED(mark)   # 値/trailを変更しない
    delete assignment[v]
    record UNASSIGN(v,color)
  record RETURN(depth)
```

baselineのtrailは常に空です。FCは上の1段だけの先行検査であり、削除を起点とする追加の伝播queueはありません。割当済み変数のdomainをcandidateへ絞る処理もありません。成功葉の後も戻り処理を通り、残りの解を探索します。故障版の省略位置だけを固定し、「どんな復元漏れでも同じ欠落数になる」とは扱いません。
