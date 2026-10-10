# 揃って測れることと、参照へ近いこと

[QE④](../../../quality-engineering-atlas/COVERAGE.md)のMSA入口。参照値10/20 arb、固定操作者A/B、各条件反復3の架空測定表。参照は教材で既知と**置く定数**であり、真値・校正traceabilityの保証ではありません。

## biasとrepeatabilityを別に見る

cell平均−参照をbias、同一参照/操作者の `s²=Σ(y−mean)²/(3−1)` をwithin sample varianceとして計算。ref誤差のMSEは `bias²+population variance(SSE/3)` であり、sample varianceとは異なります。4cellのSSEを合計/df8は有限表のdescriptive within pooled variance。等precisionは未検証で、個別cellも必ず表示します。固定操作者B−Aの平均差を参照別に示しますが、random-effects再現性分散やoperator母集団への推定ではありません。

宣言した教材分類は各cellで|bias|>1 arb、sample s²>2 arb²を別にflag、等値は内側。both/bias/spread/withinの4種類で、NIST推奨や実instrumentの合格基準ではありません。withinは有限閾値内の意味で、母集団精度や校正成功の認証ではありません。

| 手表例 | cell bias | cell s² | within SSE/df8 | 故障: 全測定のs² |
|---|---|---|---|---|
| centered | 全0 | 全1 | 1 | 28 |
| tight-biased | 全2 | 全0 | 0 | 300/11 |
| centered-noisy | 全0 | 全9 | 9 | 372/11 |
| operator-offset | 0,2,0,2 | 全1 | 1 | 320/11 |
| cancelled-bias | 2,2,−2,−2 | 全1 | 1 | 116/11 |

低分散でもbias2、bias0でも分散9。全符号biasが0でも各cell±2を隠さない。全測定を参照水準/操作者を無視して混ぜる故障版は分母11、baseline centeredでも分散28に膨らむ。参照間の差をrepeatabilityと呼ばない。`total SSE = within SSE + between-cell SSE` を分解します。これは人工参照・固定条件の算術で、製品工程ばらつきを測定したものではありません。

[手表](hand-oracle.json)/[producer作成前のSHA](qa/oracle-before-producer.json)を先に固定。producerは直接偏差平方、[checker](checker.py)はpairwise差の平方/6でcell分散、全体pair/132でnaive分散、2次momentで参照MSEを独立検算。12mutantでpooled混同/分母/bias符号/相殺/母集団再現性/真値/traceability/工程変動/RR完了/単位/MSE混同を拒否。

## 予想 → 操作 → 正常/故障比較 → 原典/実装/原票 → 答え

[実画面](index.html)で参照破線と測定点/平均の4条件図、biasと同条件分散、全体混合故障の棒図を比較。『全測定+2で比較』は1操作で実childへ送りbiasを変え、within分散が不変と分かります。これは合成値の変換でinstrument校正の実施ではありません。例/予想/JSON/resetで旧結果と全detailsを消して閉じる。古い遅延応答は復活せず、通信/child失敗は正常答えを作りません。

```sh
python3 -B checker.py
python3 -B runner.py
python3 -B qa/check-ui.py
python3 -B server.py
# 明示採取だけ新UTC原票
python3 -B runner.py --record
```

既存Python stdlib Fraction/IABのみ、installなし。正常checker/runner/QAと通常memory-only server起動/GET/POST/exportは全unit SHA/mtime不変。RAM512件、停止で失効。明示QAだけ専有QAへ保存し、新serverは新原票で再試験。source/raw/Skill/元QEを固定allowlist escaped viewerで表示、任意path不可。所有server/tabのみ終了、保護53478/60285/50835と旧unit/QE/global/manifestは操作しない。fullGate/公開/commit/pushなし。

## 原典と境界

[NIST Repeatability](https://www.itl.nist.gov/div898/handbook/mpc/section4/mpc441.htm)は同条件反復・dfで重み付けしたpoolingの入口。[Bias](https://www.itl.nist.gov/div898/handbook/mpc/section4/mpc45.htm)は参照との差・環境の影響へ。[Design](https://www.itl.nist.gov/div898/handbook/mpc/section4/mpc42.htm)のoperator/artifactの設計と比べ、2固定operatorを母集団再現性へ一般化しません。[Reproducibility](https://www.itl.nist.gov/div898/handbook/mpc/section4/mpc442.htm)の長期/日間成分は未実装。原典の実測値は流用しません。

完全Gage R&R分散成分、校正traceability、不確かさbudget、参照真値、実instrument、独立性/無作為化/等precision、製品工程ばらつき、長期安定/原因/有意性は未実証。[COVERAGE](COVERAGE.md)/[sources](sources.json)/[Skill](skills/atlas-measurement-bias-repeatability/SKILL.md)/[QA](qa/README.md)。中央受入待ち、全分野完了ではありません。
