# Atlas：実装前に決める手追跡

これは予想表であり実測ではありません。T=timeout_ms、R=retries、F=flag_enabled、P=rollout_percentの順で読む。default=(1000,2,true,50)。全層はdefault→env→taskをparseしてから合成、勝者だけはraw合成後にT/R/F/Pをparseする。

| 条件 | 全層 | 勝者だけ | 読み分ける点 |
|---|---|---|---|
| 正常境界 | 採用(5000,0,false,100) | 同じ採用 | 4勝者はtask。envの文字列も全層では検査される |
| 隠れるinteger不正 | env Tで拒否 | 採用(3000,2,true,50) | taskを採用する方針でも旧envが正しくなったわけではない |
| 隠れないinteger不正 | env Tで拒否 | env Tで拒否 | taskのR=3はTを修復しない |
| 不正な勝者bool | task Tで拒否 | task Tで拒否 | native trueは正確なintではない |
| 隠れるboolean不正 | env Fで拒否 | 採用(1000,2,false,50) | 'TRUE'は未検査で隠れる。native falseは成功値 |
| 未知field | 構造拒否 | 構造拒否 | parse/merge前に止まる。未知値は結果へ転載しない |

隠れるintegerの全層版ではSTART、STRUCTURE_OK、default4件PARSE_OK、env TのPARSE_REJECT、REFUSEの8時点。candidate/config/provenanceは全てnull。勝者版も8時点だが、3時点目にMERGE_RAWがあり、task T=3000とdefault R/F/Pだけを4回parseしてCOMMITする。event数が同じでも検査したrawは違う。

隠れないintegerの勝者版はMERGE_RAWでT/env='oops'、R/task=3を候補へ置き、最初のT parseで拒否する。候補R=3は未検査であり公開configではない。真偽値trueをTへ渡す対照はrangeの前にinteger-required。unknown-fieldはSTART/STRUCTURE_REJECT/REFUSEだけでattempts=[]、candidate=null、errorにAPP_SECRETの名だけを残す。

event数は条件順に全層/勝者で14/8、8/8、8/5、9/5、8/8、3/3の計87。成功4結果、拒否8結果。各event.indexは0から連番。詳細expectedはこの手順から固定し、producerやparse関数で生成しない。
