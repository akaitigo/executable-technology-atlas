# Atlas：実装前に手で辿った期待

これは[expected.json](expected.json)へ固定した手期待で、実測値ではありません。各結果を独立担当の別表と照合してから実行します。

leadから到達可能なroleは{lead,writer,auditor,viewer}。viewerへはlead→writer→viewerとlead→auditor→viewerの2経路があります。集合のviewerは1個です。辺を段階展開した到達と、DFSの現在経路を別に確認します。

| 条件 | 終端 | ENTER順 | LEAVE順 | active終端 | event数 |
|---|---|---|---|---|---|
| viewer単独 | accepted | viewer | viewer | 空 | 4 |
| 正常菱形 | accepted | lead,writer,viewer,auditor | viewer,writer,auditor,lead | 空 | 15 |
| visited故障 | visited-as-cycle | lead,writer,viewer,auditor | viewer,writer | lead,auditor | 12 |
| 真cycle | active-cycle | lead,writer,viewer | なし | lead,writer,viewer | 8 |
| 未知ghost | unknown-role | なし | なし | 空 | 2 |

正常菱形の2回目viewerの時点ではactive=[lead,auditor]、visited=[lead,writer,viewer,auditor]。viewerはactiveにないためREUSEです。故障は同じ状態でREJECT_REVISITに進み、reported_path=[lead,auditor,viewer]を残しますが、この列は閉じたcycleではありません。

真cycleではactive=[lead,writer,viewer]からleadへ戻ります。cycle_path=[lead,writer,viewer,lead]は入力edgeで閉じます。auditor側は拒否後に処理しません。開始roleから数学的にauditorへも到達可能なgraphですが、拒否時にその集合を利用可能closureとして公開しません。

leadの直接={approve,read}、継承={audit,read,write}、重なり={read}、有効={approve,audit,read,write}。readの付与元はauditor/lead/viewerの3roleで、viewerの経路数ではありません。viewer単独では直接={read}、継承=∅、重なり=∅です。

拒否3条件のclosure/全権限結果はnullです。空集合∅の成功、診断用部分集合、評価拒否nullを同じ表示にしません。これはpermission評価の模型で、resourceの読取り可否を決定した実験ではありません。
