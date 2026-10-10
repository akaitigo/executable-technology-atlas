# ソフトウェア工学基礎：変更の影響をどう確かめるか

この入口では、構成baselineと依存関係を使って変更後のテストを選ぶ判断を体験します。5 moduleの有限モデル1教材です。ライフサイクル、設計、測定、専門倫理を含む分野全体の完成は未主張です。

## 学習の道筋

1. **前提**：関数、整数、JSON、テストの「期待値と実値」が分かれば始められます。グラフの矢印は「利用側 → 依存先」。たとえば invoice → price は請求が価格を利用することです。
2. **主要概念と仕組み**：構成項目は config/price/invoice/report/audit。baselineはgraph・要求とtestのbinding・変更前versionを識別するSHA-256です。要求Rに対してtest Tを割り当てます。変更影響は矢印の逆方向へ伝わります。複数経路でも同じtestを重複実行しません。
3. **予想 → 操作 → 比較**：[UI](index.html)で予想を記入し、config変更を実行。税率10→20でも「0–100」は満たします。変更fileだけのT-configはPASSですが、税込110というR-price、R-invoice、R-reportは120でFAIL。closure選択は4testを実行し、失敗を発見します。独立auditは不要です。UIでprice/invoice/report/auditも比較し、変更なし・循環・未知・古いbaselineを試します。
4. **原典／実装 → 答え**：[runner.py](runner.py)のselectは逆向きBFS、[oracle.py](oracle.py)は利用側から依存先へ全simple pathを列挙。全経路の始点から到達可能性を照合します。[fixture.json](fixture.json)のR/T bindingとrawを確認します。「選んだtestが通った」と「影響する要求を満たした」は別の判断です。config変更の答えは4module影響・3要求失敗・naiveが3失敗を見落とす、です。
5. **実務判断**：変更fileだけを根拠に回帰テストを省かない。依存graphと要求bindingを更新し、受入要求を意図的に変えたなら期待値にもレビューが必要です。循環がある設計は実在しますが、このDAG限定モデルでは拒否し、SCCを扱う別分析へ送ります。古いbaselineを使って安全性を説明しない。
6. **限界**：依存は宣言された固定graph。動的import、反射、外部サービス、data/schema/build依存、未記載の結合、testの網羅性、flake、実repoの自動分析は未実証です。closure一致は宣言graph内の選択の正しさであり製品全体の安全性ではありません。変更なしで0testでも既存品質を保証しません。測定はtest数のみで、実行時間や欠陥率ではありません。
7. **原典**：[sources.json](sources.json)は下記一次資料と実装の対応を保持します。SWEBOKの構成管理は識別・変更管理・状態記録・監査を含み、本教材はその小さな断面です。

## このMacで再現する

このディレクトリでPython 3.9以降、標準ライブラリのみ。

```sh
python3 -B runner.py --case config
python3 -B checker.py
python3 -B checker.py --record
python3 -B server.py
```

通常checkerはread-only。`--record`だけが[observations/run.json](observations/run.json)を更新します。serverは動的127.0.0.1 portを表示します。そのURLをブラウザで開き、終了はCtrl-C。UIは同じPython runnerを呼び出し、JavaScriptに別の計算式を持ちません。

[Skill](skills/atlas-software-engineering-foundations/SKILL.md)はこの教材の案内のみ。[QA記録](observations/qa.json)は実画面観測とcapture保存可否を、[session記録](observations/session.json)は旧writer停止確認・専用資源終了を記録します。これらはAtlas全体のgate receiptではありません。

## 未教材coverageと次の問い

| 主要範囲 | 今回の到達点と残る問い | 次の実験（未実施） | 公式locator |
| --- | --- | --- | --- |
| ライフサイクル・工程改善 | 変更→検証だけ。要求発見、開発、運用、廃止をどう繋ぐか？ | 同じ変更を一括工程と反復工程で扱い、feedback時点と手戻りを記録 | [SWEBOK Process](https://swebokwiki.org/Chapter_8:_Software_Engineering_Process) Software Life Cycles / Process Assessment |
| 設計原則・モデル | 依存方向を読める。情報隠蔽、凝集度、結合度が影響範囲をどう変えるか？ | 直接config依存とinterface越し依存を比較し、同じ要求変更の影響module数を測る。循環をSCCへ縮約 | [SWEBOK Design](https://swebokwiki.org/Chapter_2:_Software_Design) Fundamentals / Key Issues / Quality Analysis |
| 構成管理・測定 | DAG選択とbaseline拒否。並行変更、承認、release状態、要求revision、coverage・欠陥率の意味は未実証 | 2変更branchとtest binding改訂を作り、stale evidenceを拒否。全testと選択testの時間・見逃し率を複数runで比較 | [SWEBOK SCM](https://swebokwiki.org/Chapter_6:_Software_Configuration_Management) Baselines / Configuration Control / Auditing、[Process](https://swebokwiki.org/Chapter_8:_Software_Engineering_Process) Software Measurement |
| 専門倫理・責任 | 見逃しと限界を開示する入口。誰にどの不確実性を伝えるか？ | 同じテスト結果で異なる利害関係者の架空release判断を記録し、危害・利益相反・評価の正直さを比較 | [ACM Code](https://www.acm.org/code-of-ethics) 1.2 / 2.5 |

構成管理を深掘りしてから設計変更と測定を比較し、工程と責任ある判断へ接続してください。上の4実験は計画で、現在の実行証拠に含めません。
