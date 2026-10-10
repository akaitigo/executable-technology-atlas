# 検証範囲と未教材

| 領域 | 今回の有限実証 | 未教材・次の小実験 |
|---|---|---|
| 収集欠落 | 全取得、高/低latency選択欠落、全欠落 | 実collector drop、retry、buffer overflow、sampling |
| late arrival | 固定到着4000/5000とinclusive cutoff | watermark、out-of-order、重複、retraction |
| pending/欠落 | 明示最終loss noticeと未確定の区別 | 実通知の配送保証、期限規則、識別可能性 |
| 分位点 | seen平均・nearest-rank p50/p95、空集合 | histogram bucket誤差、sketch、補間法比較 |
| 分母/未知 | 独立発行6ID、good率範囲、補完なし | 発行台帳自体の欠落・重複、未知母分母 |
| selection bias | 全既知教学Oracleとの正確な比較 | MCAR/MAR/MNARの推定、欠測補正、母集団信頼区間 |
| 実測 | memory-only Pythonと実IAB/API操作 | 実HTTP/collector/分散clock・利用者データ |
| 品質全体 | 当有限測定契約だけ | SLO budget alert、信頼性、因果、統合運用 |

全データ既知は教学Oracleだけです。collectorのfull_population_statsは未推定。確定欠落をrequestの品質失敗へ分類せず、未知latencyを0/平均へ置換しません。全Observability、全QE Atlas、Coreの完成や学習者の理解は示していません。
