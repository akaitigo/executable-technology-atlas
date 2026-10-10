# 要求と実テストをつなぐ

このPCで動く、Python標準ライブラリの有限教材です。中立なqueueの**要求ID・revision・内容 → テスト → 実行結果**を照合します。分野全体ではなく、3要求・4テスト・6ケースだけを教えます。第三者本文・実利用者データ・Credentialを保存せず、Docker／外部サービス／既存Argoのharnessを使いません。

## 起動と読み順

このディレクトリをカレントにして実行します。Python 3とブラウザ以外のRuntime依存はありません。

```sh
python3 -B test_runner.py
python3 -B runner.py --case stale-revision
python3 -B serve.py --port 0
```

最後のコマンドが出す `http://127.0.0.1:<動的port>` を開きます。終了はそのterminalでCtrl-C。ブラウザtabも閉じます。静的HTMLだけではPythonの実queueテストを実行しないため、file URLは使いません。

1. UIの問いに予測を書く（保存・採点しない）。
2. 正常を実行し、境界・orphan・旧Proof・再テスト・不具合と比較する。
3. 「要求変更直後」へ戻り、Testのpassと現在要求のCoverageの違いを確認する。
4. 生diff、個別Proofのoperation／before／output／after／expected、時刻とdigestを読む。
5. 一次資料のlocator → `queue_app.py` → `runner.py` の `execute_test`／`classify` → `oracle.py` → `test_runner.py` → UIの答え、の順に確認する。

## 比較条件

| ケース | 実queueの操作 | 最終の要求matrix |
|---|---|---|
| normal | 容量3、満杯＋1、FIFO、空dequeue | 3/3 verified-local |
| boundary | 容量1、ちょうど1件／2件目拒否、空dequeue | 3/3 verified-local |
| orphan | 旧テスト4本の後にR-DUP／T-DUPを追加 | 3/4、R-DUPはorphan |
| stale-revision | 容量3／rev1を実テスト後、容量2／rev2へ変更 | 0/3、旧Proofはstale |
| retested-revision | 同じ変更後、現在configで4本を実再テスト | 3/3、旧4Proofは保持 |
| broken-queue | overflowの拒否を意図的に無効化 | 2/3、R-CAPがfailed |

`R-CAP`には容量までの受け入れと満杯での拒否・内容保持、`R-FIFO`には受け入れ順と件数、`R-EMPTY`にはNoneと空状態を測定条件として持たせています。R-DUPは追加要求の欠落を示す教材用例であり、重複拒否を実装／検証したとは扱いません。boundaryのrev3は独立ケースの識別子です。rev1→rev2の変更履歴はstale／retestedケースだけで駆動します。

`oracle.py`はapp／runnerをimportせずtuple状態機械でqueue traceを再計算し、別の集合照合でCoverageを評価します。宣言操作の省略、raw改変、Counterの水増し、未知／重複ID、内容だけの変更もチェック対象です。独立とは**別実装**を意味し、別の人による要求承認ではありません。同じ誤解を2実装が共有する可能性は残ります。

## 観測を保存する場合だけ

通常のrunner／checker／UI実行は保存しません。更新は明示オプションです。

```sh
python3 -B runner.py --case normal --record
python3 -B test_runner.py --record
```

UIでは「今回の生観測を新しいフォルダへ保存」を自分でONにします。`observations/`へUUID付き新フォルダを追加し、旧観測を上書きしません。result・requirements・proofs・diffの実内容、実UTC時刻、Python／OS／architecture、入力とplan、8実装ファイルのSHA-256、Artifactのbytes／SHA-256を記録します。staging途中の意図的失敗で直前記録が変わらないこともcheckerが確認します。digestは変更検出であり、改竄不能な署名・安全性証明ではありません。

`app_digest`はqueue source＋config、`harness_digest`はrunner sourceです。容量変更ではapp全体を保守的にstaleとし、精密な変更影響分析やOracle sourceだけの変更まで個別Proofのstaleへ反映するものではありません。8ファイルのmetadataでその観測世代を区別します。rawログには時間を記録しますが性能／deadlineの合格には使いません。

## 一次資料のlocator（本文転載なし）

2026-10-05に公式Webで参照しました。本教材の独自例・コードへの写像であり、NASA手続への適合認証ではありません。

| 一次資料 | 読む位置 | この教材との関係 |
|---|---|---|
| [NASA Appendix C](https://www.nasa.gov/reference/appendix-c-how-to-write-a-good-requirement/) | C.2 Product Requirement、C.4 Traceability／Verifiability | 測定条件と一意な要求ID |
| [NASA Appendix D](https://www.nasa.gov/reference/appendix-d-requirements-verification-matrix/) | 冒頭のmatrix説明 | 要求と検証方法の対応 |
| [NASA SWE-052 Ver D](https://swehb.nasa.gov/spaces/SWEHBVD/pages/102695427/SWE-052+-+Bidirectional+Traceability) | §3.4 Software Design、§3.5 Software Test Procedures | 逆向きリンクと変更影響の入口 |
| [NASA Appendix E](https://www.nasa.gov/reference/appendix-e-creating-the-validation-plan-with-a-validation-requirements-matrix/) | 冒頭、validation計画の入力・deliverables | Verificationだけでは利用目的のValidation／人の承認にならない |

## Subject全体では未教材

分野全体の網羅率は算出しません。3/3はこの有限matrixだけです。要求獲得（interview／観察）、needs／goals／ConOps、優先順位と衝突解消、曖昧さ・仮定のレビュー、上位要求とinterface／設計の双方向trace、非機能／安全／security／規制要求、変更審査とbaseline承認、利用者によるvalidation、ライフサイクル管理はまだ教えていません。人の合意・要求の正しさ・製品完成は常に未確認です。

次の3実験は計画のみで、今回続けて実装しません。

1. 2つの架空needs（短い待ち時間／データ保持）の衝突と仮定を比較する。未合意を残し、人の承認を生成しない。参照: Appendix C C.3–C.4、Appendix Eの計画入力。
2. 小さな要求↔設計↔testの逆向きリンクを1つ欠落させ、変更がどこへ影響するか比較する。参照: SWE-052 §3.4–3.5。巨大ledgerや全分野Graphへ拡張しない。
3. 有限入力の性能測定と利用目的を別判定にし、verification成功／validation未確認を比較する。参照: Appendix D／E。単一PCの数値を一般的SLOや人の受容へ外挿しない。

実画面・検査・cleanupの記録は[QA.md](QA.md)、有限Coverageは[coverage.json](coverage.json)、再利用の入口は[module-local Skill](skills/atlas-requirements-engineering/SKILL.md)です。Portal rootや他Subjectを完成扱いせず、この教材で停止します。
