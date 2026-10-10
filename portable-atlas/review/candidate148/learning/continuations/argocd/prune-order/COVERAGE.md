# Argo CD：prune順序単元の対応範囲

第62分野のprune判断と、前単元 `argocd-dependency-order/COVERAGE.md` の「live-only資源のpruneや実際の適用結果」を引き継ぐ次課題です。実際の適用結果の実測は今回も未対応です。

|問い|制作・検証できた範囲|残る範囲|
|---|---|---|
|通常applyとpruneのwave順は同じか|非対称な−3/1/8を使う2対照。手計算と模型が一致。|phase混在、PruneLast、依存調整との組合せ。|
|消滅後も有効waveの数値は同じか|今回の表は初期のタスク集合と計画に固定。|各reconciliationでのタスク再生成・集合変化・有効waveの再計算。|
|逆順はwaveの符号反転か|unique prune waveの対称交換を明示。符号反転した出力の検出を確認。|任意入力の生成経路、他のwaveOverrideとの全相互作用。|
|Prunedならliveは消えているか|結果と消滅観測を別入力にし、Pruned＋削除中で後続待ちとなる1例。|最終wave後の全OperationPhase経路、削除完了時間、propagation/finalizer。|
|途中のpruneが失敗したらどうなるか|SyncFailedを仮定入力にした境界で、後続waveが未着手になる1例。|pruneObjectの全分岐、API失敗原因、retry、SyncFail hooks。|
|同waveのapplyも実行されるか|現在waveのprune失敗で同waveのapplyへ進まない1例。|複数資源の並行完了順、同waveで削除待ちとapplyが混在する実験。|
|教材を操作できるか|CLI4件に加え、readerで予想→対照→原典→答え→限界。実GUI20確認/60mouse/keyboard1、1280・390px、実capture6枚の自目視。|独立受入は別reviewerの記録で確認。操作原票と画像はGUI-QA.md参照。|
|模型の検査は再現できるか|固定手計算5例、拒否12、出力改変検出5、初回原票とhash。|Argo CDのGoコードのビルド・実行やraw byte自動契約検査。|
|pruneを実務で判断できるか|元wave/有効wave、結果/live観測、失敗境界を分離する手順。|次課題：PruneLast・削除確認・削除保護。LIVE追試は別工程。|

既存reconciliation-driftのprune有効/無効、同期Labのapply失敗、前2教材のphase/wave/依存順序との重複確認は読取のみで行いました。検索で本文が見つからないことを不存在の証明にはしていません。既存計画の受入数・統合状態・旧原票を変更していません。

全知識の網羅・Argo CD分野の完成ではありません。現在の成果と未実施項目は [observations/status.json](observations/status.json) に記録しています。
