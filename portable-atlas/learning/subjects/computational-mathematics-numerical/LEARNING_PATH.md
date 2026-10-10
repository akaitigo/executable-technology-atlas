# 数値計算を、正しい答えと誤差の区別から学ぶ

この文書は既存の [README](README.md) を置き換えない補足ガイドです。既存実装・原票・QA・source束縛は変更していません。次案は新たな実行証拠ではありません。有限教材の補足であり、分野全体の学習完了を示すものではありません。

## 1. 前提と読み順

十進数の位、二進数、指数表記、絶対値、分数、加算順序を確認します。1e16は大きさを表し、保存できる有効桁数を表しません。まず整数の総和を手計算し、その数学的な答えと、有限桁の機械が保持する値を分けてください。実装を追う時はPythonのlist・反復・関数が前提です。

入力の数学的意味 → floatへ変換した値 → 1回ごとの丸め → 加算順序と補償 → oracleに対する誤差 → 問題の感度と解法の安定性、という順で読みます。条件数は入力の変化に対する答えの感度、安定性はアルゴリズムによる誤差の増幅を調べる軸です。[著者教材 FNC: Problems and conditioning](https://fncbook.com/conditioning/) と [Stability §1.4](https://fncbook.com/stability/) が次の入口です。

## 2. 今回の仕組み・正常・境界を読む

[画面](index.html) → [READMEの観測表](README.md) → [lesson.py](lesson.py) → [Python原票](observations/python.json) → [生stdout](observations/stdout.txt)の順で読みます。再現手順はREADMEにあり、この補足作業では実行していません。

naiveは左から加算、基本Kahanは次の入力へ補償を反映、Neumaierは大小関係によって補償式を切り替え最後に加えます。math.fsumは別のstdlib方式です。方法名だけで同じ精度を保証しないでください。

正常整数例では全方式10。境界の [1e16,1,−1e16] ではnaiveと基本Kahanが0、Neumaierとfsumは1です。4項の `[1e16,1,1,-1e16]` にすると基本Kahanも2へ回復します。3項を絶対値の小さい順へ並べてもnaiveが1にならない例を残しています。これは不適切な万能規則を退ける比較であり、基本Kahan自体を意図的な欠陥実装と呼びません。NaN等の不正入力は拒否されます。

十進数文字列の厳密総和と、変換後floatの厳密総和の2つをFractionで持ちます。出力から前者を引く総誤差、後者を引く計算誤差を別に読みます。十進oracleが0なら相対誤差は未定義です。

## 3. 実務判断と限界

入力の意味、dtype・版・丸め、演算順、誤差の基準を明記し、図だけでなく数値とFractionを確認する判断に使えます。相殺を見たら最後の減算だけを責めず、途中で小さい項が失われた位置を調べます。補償・sort・許容誤差は入力契約と目的に合わせて選びます。

対象はMac Pythonの有限逐次総和です。全入力の正しく丸められた結果、正式な誤差上限、並列/GPU速度、線形solver、ODE/PDE、実データ品質は証明していません。新しいPython文書のsum説明を、既存3.9.6の観測へ転用しません。初期の誤った期待値と修正履歴は [initial-failures.txt](observations/initial-failures.txt) に残っています。

## 4. 主要未教材と問い

| 概念 | 学ぶ問い | 接続 |
|---|---|---|
| 条件数・forward/backward error | 小さな残差なら正しい解？ 問題の感度と解法の誤差を分けられる？ | 次案1とFNC §2.8 |
| 線形solver・分解・pivoting・疎行列 | 同じAx=bでも計算手順で何が変わる？ | 次案1は2×2のみ。一般解法は未教材 |
| 根探索・桁落ち・停止判定 | 同じ数式の別表現は同じ精度？ 小さい残差と根の誤差は同じ？ | 次案2とFNC §1.4 |
| ODE/PDE・安定領域・離散化 | 連続解が安定でも数値列が発散する？ | 次案3は単一ODEのみ |
| FFT・補間・積分 | 入力離散化、打切り、丸めをどう分ける？ | 専用実験と原典は未選定 |
| 並列reduction・FMA・SIMD | 同じ入力でも計算木や命令で結果が変わる？ | CPU逐次結果をGPUへ拡張しない。専用実験未選定 |
| overflow/underflow・非有限値 | 有効範囲外をどう診断・回復する？ | 今回は拒否。処理方式の教材は未整備 |

## 5. 次の3実験（すべて未実装・未実行）

1. **感度と残差**：A=[[1,1],[1,1+ε]]、既知x=[1,1]からbを作る。ε=1/10、1/10000を同じ解法で比較し、bの第2成分だけ同じ微小量δを加える。入力変化率、解の変化率、残差、厳密有理数解へのforward errorを記録する。normも固定し、残差だけで良い解を結論しない。原典はFNC [Conditioning of linear systems §2.8](https://fncbook.com/condition-number/)、Definition 2.8.1・Theorem 2.8.1。
2. **式の選択と桁落ち**：既知の離れた2根から二次多項式を作り、通常の解の公式と、大きい根を先に求め積から小さい根を求める方式を、同じfloat係数で比較する。各根の相対誤差、代入残差、係数変換誤差を分け、重根に近い入力も別条件として残す。原典はFNC [Stability §1.4.1](https://fncbook.com/stability/)、quadratic formulaのcase study・Example 1.4.1。係数丸め後の根と元の既知根を同一視しないoracleが次実装で必要。
3. **Eulerの数値安定性**：y′=−y、y(0)=1を、同じ最終時刻T=12、h=0.5/2/3でforward Euler計算し、更新数を変えて比較する。解析解exp(−t)への誤差、符号反転、振幅と更新係数1−hを記録する。h=2の非減衰とh=3の増幅を、連続系の不安定性と混同しない。原典はFNC [Absolute stability §11.3](https://fncbook.com/absstab-diffusion/)、scalar test equationとEulerの安定領域。

これらは既存総和checkerの対応機能ではありません。新実装・独立oracle・観測が必要で、3本でも分野全体は網羅しません。

## 6. 原典へ戻る・確認状況

既存実装の原典は [READMEの一次資料節](README.md) のPython 3.9、Kahan §3、Neumaier原著です。新規FNC locatorはDriscoll・Braunの著者教材として2026-10-05にread-only webで本文と節を確認しました。Pythonの [Floating-Point Arithmetic §15](https://docs.python.org/3/tutorial/floatingpoint.html) も閲覧しましたが、現行文書の版を既存runtimeの版とは扱いません。本文・図・コードの転載はありません。

探索時の `https://fncbook.com/absstab/` と `https://fncbook.com/absolutely-stable/` はweb toolで取得不能でした。取得不能を不存在とは断定せず、上の確認できた正式locatorを用います。

この追加で実験・runtime・実UI再QAを実施したとは主張しません。既存証拠のhashやsource束縛は再封印していません。
