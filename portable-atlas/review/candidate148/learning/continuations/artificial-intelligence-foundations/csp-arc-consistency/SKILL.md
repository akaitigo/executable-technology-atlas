---
name: atlas-csp-arc-consistency
description: 固定4条件のFCとAC-3について、候補削減、queue、局所supportと全解の違いを保存資料で説明する。
---

# Atlas：保存された候補伝播を読む

通常は[status](status.json)から読み、[README](README.md)→[前提](PREREQUISITES.md)→[保存計算](MEASUREMENTS.md)→[画面](index.html)→[原典・実装](reference.html)へ進む。未実行なら[手表](HAND_TRACE.md)と[契約](CONTRACT.md)までで説明し、手期待を測定結果と言わない。GUI保留中は保存JSON・コード・本文を読み、browser/serverを起動しない。GUI未確認なら操作や視認性が確認済みとは言わない。資料閲覧のために模型を起動しない。

次の6問だけを固定資料へ結び付ける。

1. 鎖A=0でFCがBまで、AC-3がC/Dへ届くのはなぜか。固定割当とsingletonの意味を先に確認する。
2. 三角A=0でB/Cがともに[1]のFC終端はなぜ解でないか。AC-3のCB削減と空停止へ戻る。
3. BCを再追加する理由は何か。CAの削減前後と残queueを辿り、BC再popは今回未実施と区別する。
4. 自由な三角で各値にsupportがあるのに全解がないのはなぜか。自由な四角の2解と手表で比べる。
5. support_testsとqueue_added/queue_skippedは何を数えるか。実時間の速さや一般計算量の実証へ広げない。
6. 取得失敗・入力拒否・模型失敗・inconsistentは何が違うか。保存値なしなら状態記録に戻る。

固定4条件を越える任意CSP、GAC、動的探索、復元、一般完全性証明、現実配置や学習済みAI性能は案内の保証範囲外。旧FCの受入と今回の新しい実測・実画面を区別する。

新しい実行は通常の読取手順と分ける。今回scopeの契約・独立期待・review済入力・資源条件とroot単独枠が揃うまで実行しない。古い資源許可は再使用しない。browser/serverは作者から起動せずroot管理の既存pageを使う。一般Agent評価は、このSkill文書と有限6問の読取確認から推定しない。
