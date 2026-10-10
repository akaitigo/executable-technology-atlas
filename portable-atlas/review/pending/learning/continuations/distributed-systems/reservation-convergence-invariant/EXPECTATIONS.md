# 先固定した契約と予想

在庫capacity（整数0〜3）、partition中の予約要求requests（0〜4件、A/B、英数の異なるID）、復旧後の直列順serial_order（全IDのpermutation）、配送schedule（A>B/B>Aの0〜6件）を入力する。初期集合は空。有限の明示scheduleを再生し、未配送を自動補完しない。

optimisticはpartition中、originのlocal集合の件数がcapacity未満ならacceptedを返して追加、満杯ならrejected。deferredはpendingを返してlocal予約集合には入れない。復旧後、独自の単一判定器がserial_order順にcapacity件までaccepted、残りrejectedを返し、origin集合に格納する。これは合意protocolの実装ではない。復旧だけでは配送されない。

判定後、A>B/B>Aのimmutable snapshotを各1件発行する。各配送はreceiverのlocal集合とsnapshotをunionし、同一messageの重複配送も記録する。delivered_setはreceiverごとの異なるmessage ID集合、delivery_countは重複を含む回数。応答履歴は不変で、acceptedを再同期で消さない。pendingは成功でも拒否でもない。

traceの各行でlocal_decision、response_event、response_history、latest_responses、accepted_returned、local_sets、pending_ids、delivered_set、delivery_count、converged、global_business_ok、replica_boundsを分離する。global_business_okはacceptedを返した異なるIDの総数≤capacity。replica_boundsは各local集合≤capacity。一致だけでは業務条件を主張しない。

基準入力はcapacity=1、A:aとB:b、serial_order=[a,b]、schedule=[A>B,B>A]。手書き表hand-trace.jsonを全行照合する。optimisticは両者accepted、復旧直後不一致、最終両者[a,b]で一致・上限違反。deferredは両者pending、復旧時は空、判定後a accepted/b rejected、配送後両者[a]で一致・上限内。逆直列順ならbが受理される。

有限schedule集合は[A>B,B>A]の2 positional permutationsと[A>B,A>B,B>A,B>A]の24 positional permutations。合わせて26 positional/8 unique schedulesで各方針の集合冪等性を検査する。これ以外の任意実行の証明ではない。空/片方向の未配送もfixtureで扱う。

model実装より先にfixture、手表、literal、独立集合oracleを固定する。oracleは配送関数を呼ばず、各trace prefixの応答と、origin受理集合・配送済snapshotの集合式から状態を再構成する。

実通信、実予約、CRDT実装、CAP証明、合意、取消・補償、durability、再起動、実時間の勝者、linearizabilityは対象外。Lamport p.559 Partial Orderingは並行eventの根拠だけで、この予約規則やunionを規定しない。
