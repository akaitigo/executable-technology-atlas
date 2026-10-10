---
name: collector-quantiles
description: collector欠落・late arrivalによる条件付き平均/nearest-rank分位点と未知・分母をこの有限moduleで再現する。
---

# 条件付き分位点を読む

README、hand-oracle、COVERAGEを読み、module内で `python3 -B verify.py` / `python3 -B route.py` を使う。原票・receiptを上書きしない。評価はmemory-only、実collectorとは扱わない。

予想→scenario/cutoff/閾値→collector seen/pending/確定欠落→教学Oracle比較→source→答えの順に読む。seen平均/分位点は条件付きと説明し、未観測latencyを0/平均に補完しない。最終loss noticeがないpendingを確定欠落にしない。欠落をrequest品質失敗へ自動分類しない。good率の分母seenと全6発行を分ける。

全データ既知は教学fixture。現実の未知を観測・補正した証拠にしない。分散実測、母集団推定、histogram/sketch、sampling、SLO運用を求められたらCOVERAGEの未教材を示す。

UIは全条件/予想変更で旧答え/raw/図を消し、reset・旧応答・拒否を確認する。既存凍結教材、Core/global/registry/設定へ変更を広げない。install・公開・commit/pushは範囲外。専用listener/tabだけ終了する。
