# Atlas：今回の範囲と残る問い

目標23のKotlin/JVM、固定期待と実装を結ぶ方針に対応する。選定時の受入基準は162件（127＋35）。[選定時に読んだ保存資料](records/selection-evidence.json)を照合し、既存教材を差し引いても、SYNCHRONIZED lazyから取得した同じ可変値の複合更新は、property教材のCOVERAGEに未対応と明記されていた。

|既存の範囲|今回との関係|
|---|---|
|lazy 3modeの逐次/2worker初期化と公開参照、例外/有限再入|初期化の同期と、取得後の値の操作を分ける前提|
|propertyのprovideDelegate/getValue/setValueと共有Slot|同じ参照が共有更新を意味することの前提|
|storageの2process更新、cryptoの2thread check/use、Configのthread snapshot|lost updateやlockの一般原理は既にある。今回の新規性とはしない|
|元Kotlin WorkbenchのAtomicInteger利用|初めてのatomic実行例とはしない|

今回の4条件は、普通のIntの分割更新、AtomicIntegerのget/set分割更新、専用lockで囲む更新、incrementAndGet。各条件の新しいLazyについて、2worker＋終了後mainの実参照、初期化回数、各1回の更新を別に照合する。[前提の説明と出所](reference.html)、[固定契約](CONTRACT.md)、[手期待](expected.json)へ戻れる。

無制御の競合発生率、CPUの複数core同時実行、任意スケジュール、複数fieldの不変条件、公平性、Coroutine/Flow、性能、他platform、一般的な可視性保証は未対応。class委譲の専用実行は別の不足である。Kotlin全体/専用Behavior全体/正式Authority分類の完了ではない。元owner未確認のため共有repoへの統合は未実施、作者の教材数加算は0。
