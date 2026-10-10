---
name: argocd-prune-order-local-lesson
description: 固定5ケースでapplyとpruneのwave順・削除待ち・失敗境界を学ぶローカル教材。
---

# pruneの順序と停止境界を手で追う

この教材ディレクトリだけで使う学習手順です。実clusterの削除操作を行うSkillではありません。前提はDesired/Live、tracked資源、Sync phase/waveです。

表は初期タスク集合に対する計画へ固定する。資源消滅後のタスク再生成と有効waveの再計算を含むcontroller全ループの実測・再実装として扱わない。

1. READMEの予想表を見て、通常applyとpruneの開始順を答えてもらう。元wave−3/1/8を符号反転する予想なら、そのまま予想として残す。
2. `python3 -B model.py --case prune-descending --view input` で入力を読む。結果・live観測は教材の仮定であり、未着手タスクではまだ観測していないと説明する。
   画面で学ぶ場合は `index.html` をfile://で開く。開始順と終端の予想を選び、段階表示→原典→答えの順に読む。予想変更やresetで古い表示を残さない。
3. `--predict high,mid,low --expect-stop consumed` を付けて対照する。effective waveが8/1/−3へ入れ替わることを手計算表と照らす。
4. `prune-waiting` と `mixed-same-wave-failed` を読む。Prunedと資源消滅、現在wave内のprune-firstと全waveの先後を区別する。待機の例は次のreconciliationの境界、失敗の例はrunTasksが戻る境界で終わる。
5. source-review.jsonの固定commit・行locatorをたどる。raw sourceのbyte hash、Go実行、API結果の自動検証はないことを保持する。未読のpruneObjectの分岐を推測で埋めない。
6. 必要なら `python3 -B verify.py` で軽い局所検査を行う。原票は上書きしない。既存の実行時hashを文書修正後のhashへすり替えない。
7. 実務判断では、元wave/有効wave、資源結果、live有無/deletionTimestamp、実際のエラー記録を分ける。削除許可や依存関係の安全性を模型から保証しない。

読み終えたら、PruneLast・削除確認・削除保護が次の未対応課題だと伝える。GUI試験を再実行する場合は専有枠を確認し、既存Chromium・専用一時profileを使って自分のcontextだけを終了する。LIVE Argo/Kubernetes、Docker、新install、サービス起動は本単元の範囲に含めない。統合・公開・受入加算や他ownerのファイル変更も行わない。
