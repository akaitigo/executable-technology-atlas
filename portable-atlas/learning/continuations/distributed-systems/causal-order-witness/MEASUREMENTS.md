# Atlas：保存した4比較

採用した初回計算は [run.json](observations/attempt-20261006T222814437915Z/run.json)。Pythonの対象1子・1回、自動retry0で、exit0、実nice10、CPU上限soft2/hard3秒、経過0.1155秒、所有子reaped・group残存なしを記録した。実通信や実clockを測った結果ではない。

| 条件 | 因果と判定した組 | 並行と判定した組 | 誤って追加した向き |
|---|---:|---:|---|
| 入力の因果辺・R1 | 11 | 4 | なし |
| 同じ辺・R2 | 11 | 4 | なし |
| 時計の大小から逆推論 | 13 | 2 | d→b、b→f |
| R1の表示順を辺へ混入 | 15 | 0 | a→d、b→d、b→e、b→f |

誤モデルも正常exit0で計算した比較である。返した分類の誤りと、実行失敗・資料の取得失敗は区別する。全15組のID/向き、経路ごとの出所、固定時計、R2の表示1→1→2→3→2→4を保存した。

[作者の保存値検証](observations/attempt-20261006T222814437915Z/verify.json)は356照合pass、6改変を拒否。共通stdout不一致だけでなく、各改変対象の分類/clock/経路source/偽陽性/再生順/bindingに対応する検査が失敗したことも残した。別担当は実装前の手表から262照合を行い、新しいproducer実行なしで保存値を確認した。独立受入の現在参照は [status.json](status.json) にまとめる。

先行資源観測 [222417](records/resources-20261006T222417890452Z.json) は通常Chrome Helperの1.6%が各browser<=1%条件を満たさず、対象0だった。閾値を変えず保持し、rootの今回限定identity決定後の [222757](records/resources-20261006T222757456529Z.json) はload3.436、idle86.39%、memory free57%で成立した。起動時age16.99秒。既存processを終了したり設定を変えたりしていない。

計算の正しさ、画面の実DOM、画像、Skillの有限利用、元repoへの統合は別工程である。実画面の確認範囲は [GUI_VERIFICATION.md](GUI_VERIFICATION.md) と状態記録を参照する。
