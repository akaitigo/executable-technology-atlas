# 検証記録

今回の問いは最短探索の条件とclosed再開の境界。経路はMac直接Python標準ライブラリ→JSON原票→loopback HTTP→実IAB。

正常・意図異常・境界の9run、入力拒否6件、options拒否5件、seed固定120格子×BFS/A*を独立集合距離層と比較する。raw.jsonは加工した図ではなくrunnerの実trace。UIはこのtraceの説明用再生。作者route.py smokeは独立AgentEvalではない。

通常checkerはread-only。原票更新は明示的 --record のみ。実行時刻・環境・hashはobservations/receipt.json、実IAB QAはobservations/ui-qa.jsonを参照。

repository全体のCore audit / publication gateはこの有限教材の完成を意味しない。全Subject完成、実ML/LLM、性能の一般化、外部サービスは未検証。専用path以外の既存差分は保全する。

## 実観測と未確認

2026-10-05 JST、Python 3.9.6 / Darwin arm64で9runを実行。costはBFS=7、Manhattan=7、過大推定=9、非整合再開あり=7、再開なし=9。同点FIFOは25取り出し、LIFOは9取り出し、双方cost=8。到達不能とstart=goal、入力拒否6件、option拒否5件、120格子のoracle比較を通過。Skill quick_validateと作者の正常/未対応routing smokeを通過。

最初のrecord検査は未生成raw/receiptへのlocal linkで失敗。明示record時だけ今回生成予定の2ファイルを許す初期生成処理へ修正し、通常checkerは全local linkの実在を要求する。失敗を探索実行の失敗と混同しない。

server起動はOS sandboxによるloopback bind拒否でexit 1。dynamic portは割り当てられずserverは残っていない。IABのfile URL表示もbrowser URL policyが拒否した。再試行・別surface・権限追加を行っていない。title/field操作、画面表示、実IAB QA、capture保存は未確認。画像は保存せず、再描画も作成しなかった。この教材の視覚入口は実表示未検証の候補であり、UI合格とはしない。

Portal/Coreの全体gateとrepoctl full verifyは、許可範囲外のCore/Portalを対象とする既存harnessを今回無視できるという依頼に従い未実行。今回のmodule checker通過から全体gate通過を推定しない。commit/push、Goal変更は行っていない。

通常の `python3 verify.py` をPYTHONDONTWRITEBYTECODEなしでも実行し、module全ファイルの前後SHA-256一覧が不変であることを確認した。checkerはimport前にbytecode書込を止める。UI JavaScriptはNode vm.Scriptで構文検査を通過したが、ブラウザ実行・表示検査とは区別する。原票更新後のreceiptはruntime検査と実IAB未確認を別欄で示す。

## 同sessionの明示承認後の実IAB QA



2026-10-05 15:28–15:31 JST、実startup出力のport 49813を用いHTTPでIABへ接続。titleとcase select/step range/buttonを現画面で確認した。BFS=7、Manhattan=7、過大推定=9、非整合再開あり=7、再開なし=9、同点FIFO=25回/LIFO=9回（cost8）、未到達、開始=目標cost0を実操作で確認。再開と抑止のstep10、frontier g/h/f/挿入順、経路を原票と照合した。不正入力6件の拒否欄、主要概念8領域の未教材coverage、次の4実験を実表示で確認。UIは固定原票を再生するため、任意grid入力formの動作確認ではない。

実captureを3回ツール出力で表示して、格子とfrontier、入力拒否、coverageと次の実験を目視した。画像ファイルはrepoへ保存していない（local pathなし）。再描画は行っておらず、画像artifact digestは存在しない。画像保存済みとは主張しない。HTTP logはpreview-http.logに保持し、raw/QA/logのdigestをreceiptへ結合した。favicon 404は保存したが教材のJSON取得は全て200。README linkもGET 200だがmain tabの文書表示へは遷移しなかったため表示合格には含めない。

自作tab 2をclose、owned serverをCtrl-Cで停止しexit0を確認した。上の初回未確認記録は当時の観測として維持し、この追加観測で実IAB QAの未完を解消した。mobile viewportと画像ファイル保存は未確認。Subject全体完成の主張は行わない。
