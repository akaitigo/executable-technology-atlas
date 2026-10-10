# Atlas：共有祖先はcycleか

固定時点の有限契約です。現在の実施状態はstatus.jsonを参照し、手期待と計算済みを分けます。

## 目的と前提

認証済みidentity・scope完全一致は前提で、新たな認証/認可強制の実験ではありません。roleから権限集合を得る段階だけを扱います。既存modelは既にvisitingとorderedを分けてcycleを検出します。増分は4role菱形・重複する権限出所・誤ったvisited判定を全固定状態へ照合する点です。一般DFS/cycle検出やscope教材を再加算しません。

## 固定graphと向き

roleは lead, writer, auditor, viewer の4個。矢印X→Yは「XがYの権限を継承する」継承先edgeです。NISTのseniorからjuniorへ辿る本教材の表示方向で、組織の直属上司関係ではありません。role自身もclosureに含みますが、入力edgeに自己edgeを補いません。

- lead→writer, lead→auditor（この順）
- writer→viewer
- auditor→viewer
- viewer→なし

cycle条件だけviewer→leadを追加します。これはleadから下った経路へ戻るedgeで、他の順序は変更しません。

直接付与はlead={approve,read}, writer={write}, auditor={audit,read}, viewer={read}。permissionは合成名で実resourceを操作しません。共有viewerへ2回到達してもroleやpermissionを二重計数しません。

## 5比較と拒否の意味

| case | graph / 開始role / 方式 | 予想 |
|---|---|---|
| viewer-only | 菱形 / viewer / 正常 | closure={viewer}, direct={read}, inherited={} |
| diamond | 菱形 / lead / 正常 | 4role成功。直接と継承の両方にread |
| diamond-visited-fault | 菱形 / lead / visited再訪をcycle扱い | viewer共有祖先を誤拒否。正常終了する設計反例 |
| cycle | back-edge / lead / 正常 | active上のleadへ戻って評価拒否 |
| unknown-role | 菱形 / ghost / 正常 | visit前に未知roleとして評価拒否 |

成功と評価拒否を返します。拒否を通常のaction denyやOS権限拒否とは呼びません。意図した拒否/故障対照もCLI正常終了内の結果です。予期しない例外や期限切れは別の実行失敗として保存します。

## 集合と表示順

正常はactive（現在の再帰経路）を先に検査し、activeでなければvisitedで処理済み共有祖先を再利用できます。visited_orderは初回ENTER順、completed_orderはLEAVE順。集合表示はrole/permission名の辞書順で、順序付きtraceと分離します。

直接権限は開始roleの付与集合。継承権限はclosureから開始roleだけを除いたrole群の付与集合で、直接権限と重なるreadを引きません。effectiveは両集合の和、overlapは積。permission_sourcesは付与元roleの辞書順集合で、全経路の列挙ではありません。leadのreadの出所はauditor,lead,viewerの3role、viewerへ至る2経路はviewerを2個にしません。

失敗時はreachable_set/reachable_order/direct/inherited/overlap/effective/permission_sourcesをすべてnullにします。ENTER済みの部分集合と現在activeはdiagnosticだけに残し、成功closureや利用可能権限へ流しません。cycle_pathは真のactive再訪だけ。故障のreported_path=[lead,auditor,viewer]は閉じたcycleではなく誤った報告経路です。

## traceと停止

STARTを最初に保存。通常はENTER/EDGE/REUSE/LEAVE、最後にACCEPTを保存します。EDGEは再帰呼出前、ENTERはvisited追加とactive push後、LEAVEはactive popとcompleted追加後です。REUSEはstateを変えません。拒否イベントはREJECT_CYCLE/REJECT_REVISIT/REJECT_UNKNOWNを区別し、その後のedgeを処理せず停止。失敗時active_at_stopは拒否位置の診断snapshotで、実threadや継続中処理ではありません。全snapshotは独立copyです。

正常のcycle検査はactive→visitedの順。故障はactiveを検査せずvisited再訪だけでREJECT_REVISITとし、他の順序/入力は同じです。再帰経路は最大4role、eventは固定41個（4,15,12,8,2）の予定です。時間計測はRBACやDFSの性能比較に使いません。

## 実行・受入・限界

手期待を実装前に固定し、独立担当はproducer/作者expectedを読む前に別の到達集合・権限表・traceを固定します。producerはexpectedを読みません。保存検査もproducerをimport/再実行しません。

Python stdlibの1子で5比較を一括出力。rootがfresh資源/単独枠/実nice>=10/5秒wall/有限回収を管理します。出力は新保存先のみ、自動retry0。作者のtarget/browser/server起動0、GUIはrootの同一pageを受けるcheckerだけです。

4role2graph/5比較の有限模型です。全RBAC、session内activation、職務分離、grant/revoke分散伝播、OAuth/OIDC、全graph正当性、NIST適合、実認証/認可強制、性能一般を保証しません。未知参照edge・任意schemaの拒否を今回の固定未知開始role比較と同一視しません。
