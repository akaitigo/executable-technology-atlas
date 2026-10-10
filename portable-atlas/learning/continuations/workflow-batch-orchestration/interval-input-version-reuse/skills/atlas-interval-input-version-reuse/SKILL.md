---
name: atlas-interval-input-version-reuse
description: 合成区間JSONの入力digestと保存結果bindingを固定し、誤cache再利用とlatest参照を有限比較する。Airflow製品、calendar、分散artifact、外部副作用には使わない。
---
README・contracts.json・expected-table.jsonを読み、route.pyの8入口へ依頼を対応づける。予想→保存済み実測→選択版/入力digest→hit/合計/保存binding→原典と答えを辿る。
正常keyはtask実装label・interval・正規化input digest。入力版labelは参照で、同名が同内容だと仮定しない。cache artifact digestはbinding/value/countの内容照合で、入力digestとは分ける。
区間欠落は同じ入力でも別区間artifactを返し得る。数値が一致してもbindingを照合する。digest欠落は別内容を旧値5へ誤再利用する。latest-lookup故障は明示v1をlatest v2へすり替える別の参照故障。
通常checker/runnerは全hash/mtime不変、結果stdoutのみ。明示再記録だけrunner.py --recordでfresh runを作る。UI比較は原票readerで計算やcache更新を再実行しない。予想だけの変更でも旧比較/答え/traceを消す。
cache content改竄は入力拒否として合計を出さず旧cacheを保持。読取失敗はexecution-error、正常答えなし。Airflow原典は固定partitionと再実行の動機で、独自cache方式の製品保証ではない。
Airflow起動、calendar、分散storage、外部効果、耐久性、権限/公開/課金は除外。README次coverageへ案内し、Skillから実操作許可を推定しない。
