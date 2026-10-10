---
name: rv32i-hazard
description: ADD/ADDIのRAWを有限5段pipelineで学び、無対策・stall・forwardingのcycleと逐次結果を比較する。
---

# RV32I RAWの有限実験

このmoduleのREADMEとCONTRACTを読む。Python標準libraryだけでserve.pyを起動し、表示された自分のlocalhost URLを開く。既存serverやtabは停止しない。

最初にchain/無対策でoracleとの一致を予測して実行し、ID-latchが古い理由を説明する。stallで4回の待ちを数え、WB→ID順序を確認する。forwardingのMEM経路を追い、priorityでMEMがWBより新しい理由を説明する。two-source、wb-gap、x0-write、即値境界、wrap、emptyを比較する。

逐次oracleの全register、cycle表、raw JSONを実際に照合する。verify.pyとroute.pyはread-onlyで既存証拠を検査する。既存receiptや初回rawを上書きしない。変更が必要なら同じmodule内で旧証拠と新しい観測を分ける。

全RV32I、機械語、LOAD/branch、HDL、実CPU速度への主張を広げない。sandbox bind/connect拒否は実測失敗として扱い、正式なOS permission経路以外で回避しない。検証後は自分のserver/tabだけを終了する。
