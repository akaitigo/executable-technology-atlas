---
name: atlas-lazy-mutable-counter
description: Atlasの保存した4条件からlazyの初期化と可変値の複合更新の境界を読む。
---

# Atlas：初期化と更新を分けて案内する

まず [状態記録](status.json) を読む。実測がない場合は [契約](CONTRACT.md)・[手期待](expected.json)・[原典の案内](reference.html)・[コード](src/LazyMutableCounter.kt)までで止まり、予想を測定値として答えない。実測がある場合は状態記録の実行ログを読み、GUIが未確認ならテキスト経路で案内する。閲覧のためにcompiler/browserを自動起動しない。

1. なぜinit1・同じpayloadでもfinal1か。plain-splitの2workerのread0とwrite1、Barrier前後を読む。lazy初期化の同期と更新は別と説明する。
2. AtomicIntegerでもget/set分割は安全か。atomic-splitの同一storage参照と各操作の値から、組合せ全体のatomic性がないと説明する。
3. lock版のどこを囲むか。lock前で待ち、read+writeを同じ専用lock内に置く。勝者は固定せず(old,new)集合を示す。
4. incrementAndGetのoldは分かるか。実返値{1,2}は読めるが、別getのoldを実測したことにしない。
5. 本当に並行処理か。2つの異なるworker thread IDと各1更新を示す。複数core同時実行、回収順をCPU全順序とする説明はしない。
6. どの前提/限界へ戻るか。[前提](reference.html#prerequisites)からlazy公開/property共有/既存thread・process教材の違いを読み、[未対応](COVERAGE.md)へ戻る。任意payload/複数field/Coroutine/Flowの安全性へ広げない。

新実測は [実行条件](RUN_CONDITIONS.md) の現在資源・排他・固定cache・優先度・時間・回収を満たして新記録へ保存する。Skill文書や6問の有限読取確認は、未知質問に対するAgent一般評価ではない。
