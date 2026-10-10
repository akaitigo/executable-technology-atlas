# 形式手法を、状態と反例から学ぶ

この文書は既存の [README](README.md) を置き換えない補足ガイドです。既存の実装・原票・QA・source束縛は変更していません。有限教材の補足であり、分野全体の学習完了を示すものではありません。以下の次実験はすべて未実装・未実行です。

## 1. 前提から主要概念へ

集合、真偽値、状態の組、graphの頂点と辺を読めれば始められます。状態はその時点の変数の値、遷移は許された1回の変更です。まずP0/P1の位置pcと共有ownerを書き、どの条件で入室できるかを手で確かめます。実装を読む場合はPythonの関数・tuple・queueが前提です。

初期状態 → guardと原子的step → 到達状態 → 不変条件 → 反例 → 進行条件、の順で読みます。不変条件はすべての到達状態で保ちたい性質です。「ownerは1つ」というデータ型の制約だけでは、2人のpcが同時にcriticalでないことを保証しません。

Safetyは悪い状態へ到達しないこと、livenessは求める進行がいつか起きることを問います。全状態を調べるmodel checking、規則から導く証明、具体実装を抽象仕様へ対応させるrefinementは、対象と根拠の異なる作業です。

## 2. 既存の正常・意図異常を読む

[画面](index.html) → [READMEの観測説明](README.md) → [model.py](model.py) → [生stdout](evidence/stdout.json) → [実行identity](evidence/run.json) → [COVERAGE](COVERAGE.md)の順で辿ります。起動・再現方法はREADMEにあります。この補足作業では起動・checker実行を行っていません。

正常モデルは空き確認と入室を1つのatomic stepにします。意図異常は確認からclaimまでを分け、claim時のguardを省きます。その間に別processが進むと、両者が昔の「空き」を根拠に入れます。保存観測は正常8状態/14遷移/違反0、欠陥23状態/44遷移/違反2、最短反例6遷移です。探索は最初の違反後も続けています。

保存traceのUIはPython結果の再生です。実threadやOS mutexの観測ではありません。全到達探索はこの有限domainに対してであり、process数・値の範囲を変えた証拠ではありません。別照合も同じtransition関数へ依存し、独立形式証明とは扱いません。

## 3. 実務で問えることと限界

checkとuseの間で前提が変わるか、どの操作をatomicと仮定したか、守りたい条件が変数の型だけで表せるかをreviewできます。反例では状態だけでなくsource/target/action/processを読み、仕様の仮定とコードの操作境界を照合します。

safetyが通っても、待つprocessの進行は別です。P1をwaitingに置き、P0だけが繰り返すscheduleは相互排他を守りながら飢餓を起こし得ます。公平性の対象と強さを宣言する必要があります。実CPUのatomic命令・weak memory・故障・性能への写像は未検証です。モデル合格だけで実製品の安全性を判断できません。

## 4. 原典へ戻る

- Lamport著者教材 [Session 8: Mutual Exclusion](https://lamport.azurewebsites.net/tla/tutorial/session8.html)、§1.1 The Problem／§1.2 A Warning／§2.1 The Algorithms' Form：相互排他と操作境界。既存の [sources.json](sources.json) に対応を記録しています。
- [Session 9: Liveness](https://lamport.azurewebsites.net/tla/tutorial/session9.html)、§1 Safety versus Liveness／§3 1BitMutex／§4 Starvation Freedom：進行の性質とfairnessを読む入口です。今回のPythonモデルをPlusCal/TLC実行と呼びません。
- Software Foundations著者教材 [Hoare Logic, Part I](https://softwarefoundations.cis.upenn.edu/plf-current/Hoare.html)、Hoare Triples／While Loops：状態の列挙から、事前・事後条件と不変条件の規則へ進む入口です。

## 5. 未教材の具体概念と問い

| 主要未教材 | 学びたい問い | 次への接続 |
|---|---|---|
| temporal logic・fairness・starvation | 誰のどの動作を公平に選ぶ？ deadlock freedomなら全員進める？ | 次案1、Lamport Session 9 |
| deadlock・livelock・資源待ち | 動けない状態と、動き続けても進行しないcycleは同じ？ | 次案2 |
| Hoare logic・定理証明・termination | 有限例の一致と、任意の入力への帰納的証明は何が違う？ | 次案3、Software Foundations |
| refinement・weak memory | 宣言したatomic stepは実コードの何に対応する？ | 既存COVERAGEのrefinement gap。写像実装は未整備 |
| state explosion・partial-order reduction | 独立な操作の順を省略しても、調べる性質を保てる？ | 専用原典・比較実験は未選定 |
| parameterized verification・分散protocol | 2processの結果を任意人数や故障ありへ拡張できる？ | 有限domainの変更には別検証が必要 |

## 6. 次の3実験（未実装・未実行）

1. **進行と公平性**：2processの有限mutex graphに「P1がrequestした後、criticalへ進む」を追加する。公平性なし、process単位のweak fairness、入室action単位のstrong fairnessを別仕様にし、待機が残る到達prefix＋cycleを比較する。各actionのenabled履歴と実行履歴を残し、公平な反例かを独立に判定する。公平性を追加すれば常に全員進むとは予想しない。原典locatorはLamport Session 9 §3–5、StarvationFreeとSemaphore Liveness。strong fairnessの厳密定義は次実装で追加原典確認が必要です。
2. **2lockの待ち**：P0がL0→L1、P1がL1→L0の順に取得する有限モデルと、両者がL0→L1に揃えるモデルを比較する。未完了なのに非stuttering遷移が0の状態、そこへの最短trace、解放可能な状態を記録する。さらに「取得失敗で解放してretry」のcycleを進行なしとして区別する。原典locatorはLamport Session 9 §3、DeadAndLivelockFreeの進行条件。この独自2lockモデルは原典algorithmの再実装ではありません。
3. **ループの証明と有限試験**：自然数nからx=n、y=0として、xを1減らしyを1増やすループを別教材で作る。不変条件x+y=n、終了時x=0を、更新規則から導く。yを2増やす欠陥との有限n=0..8比較も行い、帰納規則と反例を分けて記録する。Hoareのpartial correctnessだけで停止を示したとはせず、自然数xの減少を別に扱う。原典locatorはSoftware Foundations Hoare、While Loops。Rocq/Coq等による機械証明はさらに別作業です。

3本でも形式手法全体は網羅しません。既存checkerにこれらの検査があるとは扱いません。

## 7. 資料と検証の状態

2026-10-05にread-only webでLamport Session 9の本文・節、Software Foundations Hoareの本文とWhile Loopsを確認しました。今回の新規locatorに取得失敗はありません。Session 8の対応は既存sourcesに基づき、この追補で再取得したとは主張しません。第三者本文・図・コードは転載していません。

確認したのは文書と静的リンクです。実験、runtime、実UI再QA、形式証明、repository全体の完成判定は追加していません。既存証拠のhashやsource束縛は再封印していません。
