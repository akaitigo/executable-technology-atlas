# 異常点を取り込むと、管理限界が逃げる

[QE④](../../../quality-engineering-atlas/COVERAGE.md)の合成工程管理図入口。有限合成baselineから中心/ばらつきを推定し、固定して後続値を見る。異常点を含め毎回再推定する故障版と、同じ入力で比較します。旧教材/親QE/global/manifestを変更しません。

## Phase Iの推定とPhase IIの利用

baselineは4..12整数、monitoringは1..8整数、−50..50 arb。母σは未知、baseline平均と `s²=Σ(x−mean)²/(N−1)` を推定し、未補正のsを代用して `mean±3s` を固定する教材模型です。NIST IndividualsのI-MR/d₂やs/c₄方式は実装していません。s²とsの不偏性は別で、sはσの不偏推定量ではありません。少数合成点でPhase Iの統計的安定は未確認。baselineの除外/cleaningや実データ受入も未実施です。

Phase IIで点を追加しても正常版のmean/s²/限界は不変。故障版はbaseline＋その時点までのmonitoring（現在点を含む）で毎回再推定し、その現在点を判定する。未来点は含めません。仕様は別宣言の2整数上下限、工程の推定値から作りません。

判定は `(y−mean)² > 9s²` をFractionで厳密比較。等値は内側。平方根は図と小数限界の表示だけで、丸めた線で判定しません。N−1をNへ替えません。baseline不足は拒否、zero s²もzero-variation拒否で、幅0を安定/確率0とは扱いません。

## 実装前手表と反例

baseline `[7,7,10,13,13]`: N5/mean10/SSE36/s²9/半径平方81/LCL1/UCL19。点19/1は等値で内側、20/0は外側。点20を含む故障版はN6/mean35/3/s²358/15、20は内側へ隠れます。仕様0/20では20が仕様内でも管理線外。仕様9/11では13が管理線内でも仕様外。14が3連続の例は単一点規則では検出しません。run/trend規則は未実装で、内側=安定とは読めません。

[手表](hand-oracle.json)と[producer前SHA](qa/oracle-before-producer.json)を先に固定（初回手表の故障版s²誤算は独立検算で検出し、[旧手表](qa/hand-before-arithmetic-repair.json)/[訂正票](qa/hand-correction.json)を保持して訂正）。producerは偏差平方、[checker](checker.py)はpairwise差と整数交差積 `(N*y−sum)²*(N−1)>9*pair*N` で独立検算。分母/境界/spec取り違え/再推定/原因断定など12mutantを拒否。[契約](contracts.json)外のbool/float/NaN/Infinity/duplicate/unknown keys/pathを拒否。

## 予想 → 操作 → 正常/故障比較 → 原典/原票 → 答え

[UI](index.html)はbaseline灰、monitoring青/外側赤、管理線青破線、仕様線橙点線、固定線と逐次故障線の2図を表示。『20を追加して比較』は1操作で入力を追加し、実childへ送信して判定変化を示す。JSON/例/予想/明示resetは旧図/表/原票/答えを消してdetailsを閉じる。遅延応答を変更後へ復活させず、失敗は正常答えを作りません。

```sh
python3 -B checker.py
python3 -B runner.py
python3 -B qa/check-ui.py
python3 -B server.py
# 明示採取のみ新UTC固定raw
python3 -B runner.py --record
```

通常checker/runner/QAとmemory-only serverの起動/GET/POST/exportは全unit SHA/mtime不変。明示QA採取だけ専有QAへ保存。server RAMは512件まで、停止で失効。viewerは固定allowlist escaped textだけ、任意path不可。新serverは新原票を使う。所有server/tabのみ終了し、保護53478/60285/50835は操作しない。既存Python stdlibのみ、install/commit/push/公開/fullGateなし。

## 原典と未実証

[NIST Control Charts](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc31.htm)は中心/限界とpatternの考え方へ、[Variables Control Charts](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc32.htm)は分母N−1、sとσ、仕様との差、再推定の注意へ。[Individuals](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc322.htm)のI-MRとs/c₄は今回と異なる未実装方式。[Phase I/II記述](https://www.itl.nist.gov/div898/handbook/pmc/section5/pmc543.htm)の歴史値分析/後続監視を用語の入口にします。

原典の実測値や確率を流用しません。正規性/独立性/誤警報率/ARL/母σ/工程安定/原因特定は未検証。外れはこの有限規則のsignal、原因確定ではない。工程能力/測定系/run/trend/重み付き監視などは[COVERAGE](COVERAGE.md)へ。[Skill](skills/atlas-frozen-baseline-control-limits/SKILL.md)/[QA](qa/README.md)/[sources](sources.json)。中央受入待ち、QE既存受入数や分野完成は増やしません。
