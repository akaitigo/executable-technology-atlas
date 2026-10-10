# Atlas：固定FIFOのAC-3手順

`neq(x,y)`はx≠yだけです。domainとqueueの記録はcopyします。FCとAC-3は同じ入力の別copyから開始し、FC結果をAC-3へ渡す連続処理ではありません。

```text
FC(domains, fixed_assignment):
  for a in fixed_assignment のID昇順:
    for n in neighbors[a] のID昇順:
      if n is not fixed:
        for y in sorted COPY(domains[n]):
          constraint_tests += 1
          record CHECK(a, fixed_assignment[a], n, y)
          if fixed_assignment[a] == y:
            remove y; removed_values += 1; record REMOVE
        if domains[n] is empty:
          empty_domain_stops += 1; record EMPTY; return
  record END

AC3(domains):
  Q = sorted unique directed arcs
  in_queue = set(Q)
  initial_arcs = len(Q)
  record INITIAL
  while Q is not empty:
    (i,j) = pop_front(Q); remove (i,j) from in_queue
    revise_calls += 1; record POP
    changed = false
    for x in sorted COPY(domains[i]):
      supported = false
      for y in sorted COPY(domains[j]):
        support_tests += 1; record SUPPORT_TEST(i,x,j,y,x!=y)
        if x != y:
          supported = true
          break
      if not supported:
        remove x from domains[i]
        removed_values += 1; changed = true
        record REMOVE(i,x,reason=no support in current domains[j])
    record REVISION_END(i,j,changed)
    if domains[i] is empty:
      empty_domain_stops += 1
      record EMPTY(i, remaining Q)
      return inconsistent
    if changed:
      for k in sorted neighbors[i] excluding j:
        if (k,i) not in in_queue:
          append (k,i) to Q; insert into in_queue
          queue_added += 1; record ENQUEUE(k,i)
        else:
          queue_skipped += 1; record ALREADY_QUEUED(k,i)
  record END
  return arc-consistent
```

`arc-consistent`はこの固定二項入力の各値に相手候補がある状態を指します。全体に一つの共通割当がある、という結論ではありません。`inconsistent`は候補削減による空domain検出で、入力の形式拒否やprocess失敗とは別です。全解集合の証拠は実装前の手表へ戻ります。
