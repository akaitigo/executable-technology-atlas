---
name: kotlin-smart-cast-boundaries-learning
description: Kotlinのmutable property・custom getterとローカルvalを比べ、smart castの条件と一度読んだ値を使う判断を学ぶ。固定期待値と保存した実測を区別する。
---

# smart castの境界を学ぶ

1. observations/status.jsonを読み、制作と実行の状態を確認する。今回のcompile3/runtime6・独立49項目passはリンク先の実測原票で確認し、固定期待値だけを実測証拠として紹介しない。正常5/runtime NPE1/compile拒否2を分ける。
2. READMEの到達目標と前教材のString?比較をつなぎ、propertyを何回読むか予想する。操作画面は127.0.0.1の静的serverから開き、条件と予想→原票読取/比較→原典・実装→答え/限界の順に進む。
3. var property／custom getterの拒否例と、local val snapshotのコードを読む。compile拒否とruntime NPEを分ける。
4. getter-snapshotの後半の読取りは、利用後の比較用であることを説明する。snapshotを使うために再読取りが必要だと教えない。
5. まず保存原票をverify.pyで読み、不要な再実行をしない。新たな実行が許された枠では、現行resource_gate.pyの全体CPU・load・メモリ・既知重処理の条件を確認する。sandboxで無害なreadが阻害された場合は同じreadを正規reviewへ回し、拒否なら迂回しない。実行時は既存固定cache、nice実値10以上、heap/processor設定、短いtimeoutを守り、代表成功と資源再確認後に同じattemptで有限ケースを逐次実行する。旧CPU25%/process閾値は再利用しない。
6. 作者GUI QA 24項目・実capture 7枚の目視は保存記録を読む。必要な追加GUI検証は許可された専有枠で既存browserだけを使い、取得失敗をruntime異常と混同せず、予想/条件/reset後の古い結果残留を確認する。終了後に自分のcontext・profile・一時loopback serverを終了し枠を返す。SDK・OS設定・他process・既存教材は変更しない。独立受入は別reviewerの判断を待つ。
7. 実務では一度読んだ値と最新値のどちらが必要かを問う。deep copyや複数fieldのatomic snapshot、全propertyの安全性を保証しない。次は未教材coverageへ進む。
