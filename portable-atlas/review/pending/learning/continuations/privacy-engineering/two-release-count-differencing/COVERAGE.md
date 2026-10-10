# 2release差分の有限coverage

[元Privacy実験3](../../../subjects/privacy-engineering/LEARNING_PATH.md)の独立継続。架空A/B/C count2時点、対象1追加/残存を共通知識、背景add/delete各≤2、削除はbaseline分だけ。最大300count-vector候補を全列挙しcategoryがknown/ambiguous/inconsistentかを見る。単一差分+1だけで背景変更を無視する故障を比較。

未実施: 実人物/実dataset/外部linkage、公表、現実の再識別率/個人対応/背景record身份、法的適合、対象存在の観測からの推定、任意変更の無限候補、DP mechanism/noise/epsilon/accountant、privacy保証、現実のauxiliary知識妥当性。候補数は確率ではない。0候補は前提不整合、曖昧は安全保証ではない。直接ID無しでも有限category推論は残り得る。既存RRとは別のrelease組合せ問。中央受入待ち。
