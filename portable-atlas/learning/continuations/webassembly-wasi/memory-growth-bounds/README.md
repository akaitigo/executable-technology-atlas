# WebAssembly memoryの増設と境界

前提はbyte添字、page、ArrayBufferとview。[元教材のWasm数値境界](../../../subjects/webassembly-wasi/README.md) → このUIで予想・実行・比較 → [実装前の手表](hand-oracle.json) → [独立oracle](oracle.py) → 原典 → 答えの順。[Browser実観測と説明モデル](../../../subjects/browser-engine-web-runtime/README.md) はNode結果をBrowser観測へ代用しないための関連教材。

## 固定した入力と観測

72byteの手生成core moduleは非shared memory32 min1/max2、default fixed ArrayBuffer。1page=65536bytes。hostで0=7、65535=171を書く。export load8は実i32.load8_u、growは実memory.grow。初期65535は171、65536はRuntimeError trap。JS memory.grow(1)は旧page数1を返し2pageへ。新65536/131071は0、131072はtrap。旧byte値は増設後も新viewで読める。

grow後の旧ArrayBuffer.byteLengthと旧TypedArray.lengthは0、添字読取はundefinedで例外ではない。一方旧TypedArray.sliceと旧DataViewのbyteLength/getUint8は実TypeError。JS grow(2)でmax超過はRangeError、core grow(2)は−1。両方とも1pageと旧viewを保持する。この成功は今回の資源状況での観測であり、max未満のgrowが常に成功する保証ではない。

host addressはnumberの整数0..131072。範囲上端は意図的trapを試すための許可値で、アクセス可能という意味ではない。bool/string/null/配列/小数/範囲外はinstantiate前に拒否。基盤失敗条件はhost executor Errorを明示注入し、未instantiate・結果なし・正常答え破棄として表示する。実際のBrowser停止を起こした証拠ではない。

## 再現する

```sh
python3 -B verify.py
python3 -B route.py
python3 -B serve.py
```

UIの「Browserで実行」はそのBrowserで新instanceを作って実行する。通常checker/routeは保存Browser rawと固定手表/byte列を読むだけで、Wasmを再実行せず原票を書かない。新記録は別の実Browser操作から実rawを採取し、未使用 `--record attempt-01` を明示する。この原票はIABツールの実JSONを手転記したもので、PythonがBrowserを起動した記録ではない。7条件50API event、host入力8拒否、6改変拒否を照合。時刻は実行の識別用で性能を評価しない。

予想変更は新値を保持し前比較・答えdetails本文を空にして閉じる。条件変更は前結果も消す。位置拒否は開いた答えと比較を保持する。応答保留は実行済み結果を手動で待たせ、条件変更後の旧ticketを採用しない有限UI検査。ネットワーク・並行thread・実runtime内部traceではない。

## 原典と実用判断

[Core execution memory instructions](https://webassembly.github.io/spec/core/exec/instructions.html#memory-instructions) のload8の境界trap、memory.growの旧size/−1を参照。[Core memory allocation/growth](https://webassembly.github.io/spec/core/exec/modules.html#grow-mem) と [JS API Memory.grow](https://webassembly.github.io/spec/js-api/#dom-memory-grow) のRangeError・fixed buffer refreshをbyte/page手表と対応させる。仕様本文や図を転載しない。

grow後はmemory.bufferからviewを取得し直す。undefined、TypeError、RuntimeError、RangeError、coreの−1、host拒否を一種類の失敗に潰さず、呼出し境界と値を保存する。WASI権限、共有/resizable memory、性能、全engine互換は未実証。元README E1のmemory.grow/boundsだけを埋め、ABI pointer/length、table、GC、SIMD、threads等は残す。Subject/Atlas全体の完了ではない。

次はpointer/lengthの範囲を往復検査、shared memoryを別fixtureで比較、複数engineで同binaryを検証する。

アドレス編集中の旧答え残留を実IABで検出し、input時resetへ修正。初期appと失敗観測を保持し、最終版7条件を再実行した。保護listener 60285は他owner側でPIDが49275から53612へ変わった。こちらは操作せず、前後の実PIDを記録した。

独立QAのP2修理: LOAD_OK/trapの答えは実load eventのaddress/value/errorを使う。2load条件×0,1,65535,65536,131072の実Browser再実行と入力resetをaddress-revision-rawへ保存。旧30fileとmtime/hashはhistory/manifestへ保全した。
