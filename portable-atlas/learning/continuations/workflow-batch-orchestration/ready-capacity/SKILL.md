---
name: atlas-workflow-ready-capacity
description: Atlasの有限DAGで、依存待ちとworker容量待ち、早すぎる完了通知を保存結果から区別する。
---

# Atlas｜DAGの待ちを読むSkill

[読む順](README.md)→[学習画面](index.html)→[保存した計算結果](observations/run-01/results.json)→[原典と実装対応](SOURCES.md)→[範囲](COVERAGE.md)の順で使います。保存結果が未作成・照合できない場合は、[手予定表](expected.json)を実測扱いせず、その不足を伝えます。インストール、外部サービス、実workerの起動は行いません。

1. 「CとDが待っている。どちらもworkerを増やせば動く？」には、`capacity-one` のt=1を開く。Cは `ready-capacity`、Dは `dependency-wait`。次に `capacity-two` のt=3で空き1枠でもDが待つことを読む。依存と容量を別の判断として答える。
2. 「全仕事が4tickで終わったので高速化に成功した？」には、`done-on-start` のt=0と3、`dependencyViolations` を読む。A→B/B→Dの違反と、t=3の通知済み4件に対する実完了2件を確認する。`is_active()`だけで実workerの完了を推定しない。対照の `simultaneous-finish` はBのdurationを変えた別条件だと説明する。
3. 「この結果なら本番でも最速・公平で、失敗しても安全？」には、[契約の固定条件](CONTRACT.md)と[未対応](COVERAGE.md)へ案内する。実並列性能、最適性、公平性、再試行/復旧、分散副作用の検証はない。前提の[逐次DAG教材](related.html?topic=dag)にあるretryも、一般のexactly-onceへ広げない。

予想→時刻の操作→対照→原典/保存実装→答え→限界の順を保ちます。計算と実GUIの確認状態は[状態記録](qa/reader-acceptance.json)で分けます。この3例の読取利用は一般Agent評価や未知の質問への正答保証ではありません。

Atlas の保存計算は4条件18境界・6拒否まで実行済みで、保存readerの実GUIと1280/390の画像8枚も確認しています。このSkillの3例は独立担当が保存値・前提・原典・未対応への導線を読取利用しました。最終受入と保存記録は[確認状態](qa/reader-acceptance.json)から辿れます。
