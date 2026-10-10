# Atlas：一つのreadの規則

`ways=1`はdirect、`ways=2`は2-way。set_count=16/(4*ways)。全入力の形・addressを先に検査し、各方式は新しいinvalid状態で始める。

```text
for address in the fixed trace:
  before = deepcopy(all sets and recency lists)
  block, offset = divmod(address, 4)
  tag, set = divmod(block, set_count)
  selected = first way (ascending) whose valid and tag match
  hit = selected exists
  victim = null
  if not hit:
    selected = first invalid way (ascending)
    if no invalid way:
      selected = recency[set][0]   # LRU
      victim = lines[set][selected].block
    lines[set][selected] = valid block/tag and its 4 memory bytes
    fetched = 4
  else:
    fetched = 0
  if not hit OR mode is not deliberate_no_hit_touch:
    remove selected from recency[set] if present
    append selected to recency[set]  # now MRU
  returned = lines[set][selected].bytes[offset]
  record mapping, decision, before, deepcopy(after), returned, fetched
```

hitを更新しない故障だけはhit-recency traceへ適用する。先頭invalidを選ぶ規約はcold startのway名を一意にするための教材上の決め事で、原典の全実装に要求するものではない。victimがnullでもblock0が入っている場合を区別し、truthy/falsyでblock0を空と判定しない。

手表は各read後の選択setのblock列とLRU→MRU way列を記す。beforeは直前の同set状態、他setは変わらない。各rowを別値として記録し、後から追加した結果で期待を書き換えない。
