# 小さなWebAssemblyで数値と境界を学ぶ

問い：JSの足し算をi32.addへ移すと何が変わり、どの段階で異常が拒否されるか？ 手生成41byteのcore moduleを実Browser/NodeのWebAssembly APIで動かす有限教材です。WASI・Component・全runtime互換性は未実行、Subject全体は`incomplete`です。

## 学習の道筋

1. 前提：関数・整数・JS Number・16進byteを知る。Wasm compilerやSDKは不要。
2. 予想：`2147483647 + 1`はJS Numberと同じか、例外になるか？ inputの型・範囲を考える。
3. 主要概念と仕組み：magic/version、type/function/export/code section、型付きoperand stack、instantiate/import、JS値変換を区別する。
4. 実装と正常/異常：固定12入力をUIで実行。正常・上限下限・小数入力変換、bad magic/type/import、BigInt入力を別々に比較する。
5. 実務判断：i32のwrappingが用途に合うか、JS境界で整数/範囲検査が必要か、失敗がcompile・link・invokeのどの境界かを判断する。例外classが同じでも原因はrawとbinaryから見る。
6. 限界：stack図は説明モデルで内部engine Traceではない。これだけでメモリ安全、権限、全整数/浮動小数、速度優位、全runtime互換性を保証しない。下のE1–E4へ進む。
7. 原典→[binary](binary.mjs)→[実runner](experiment.mjs)→[独立oracle](oracle.mjs)→[入力](cases.json)→[検査](check.mjs)へ戻って説明と実測を区別する。

## 使い方

このdirectoryで、既存Nodeを使用します。依存install不要。

```sh
node verify.mjs
node check.mjs
node serve.mjs
```

serverのloopback URLをBrowserで開き、予想→選択実行→表/raw/説明stack→原典→答えへ進む。UIはそのBrowserのWebAssemblyで本当にinstantiate/export呼び出しし、Node原票をBrowser結果として表示しません。Nodeの実結果はverifyのrawで別保存します。

新原票が必要な時だけ`node verify.mjs --record observations/未使用名`、実Browser操作raw/screenshotを別の未使用directoryへ保存。`node check.mjs --node observations/新Node/raw.json --browser observations/新Browser/raw.json`で照合し、checker自身の記録は明示`--record observations/未使用名`のみ。既存directoryへの上書きは拒否、通常はread-only。Sourceが変わったら旧原票を保持してNode/Browserを実再実行し、digest追記だけで通さない。

## binaryとoracle

正常binaryのtext表現（生成コードが実Uint8Arrayを作り、実bytes hashを原票へ記録）：

```text
00 61 73 6d 01 00 00 00          magic / version
01 07 01 60 02 7f 7f 01 7f       type (i32,i32)->i32
03 02 01 00                      function type index 0
07 07 01 03 61 64 64 00 00       export add → function 0
0a 09 01 07 00 20 00 20 01 6a 0b code: locals=0 / local.get 0,1 / i32.add / end
```

正常/境界8入力、拒否4入力。bad-typeはoffset16を0x7e（i64）へ変え、i32命令と結果型を矛盾させる。missing-importは別39byte moduleがenv.add関数を要求し、host `{env:{}}`でLinkErrorになる。BigInt入力は正常moduleへ1nを渡してTypeError。安全なテスト入力のみ、外部素材なし。

独立oracleはWebAssemblyもbitwise演算も使わず、BigIntの数学的modulo 4294967296とsigned解釈で照合。byte配列はgeneratorとは別のliteral hexで固定する。JS Numberとの差は大整数精度一般の証明ではなく、今回の固定入力の比較。stackはoracleの説明モデル、実raw eventsはAPI呼び出し段階の記録です。

## 次に何を学ぶか：主要未制作coverage

|案|概念・問い|次の具体的実験／未実行|公式locator|
|---|---|---|---|
|E1|memory/ABI/table/trap/GC/SIMD/threads：hostとの資源・値の境界は？|memory.growとbounds trap、pointer/length roundtrip、型別入力を小moduleで実行し、共有memoryは別の実験条件へ分離。今回はmemory/table/SIMD/GC/threadsなし|[Core memory](https://webassembly.github.io/spec/core/syntax/modules.html#memories)、[Core execution](https://webassembly.github.io/spec/core/exec/instructions.html)|
|E2|WASI interface/capability/filesystem/clock/network：hostが渡さない資源は拒否されるか？|WASI versionとruntimeを固定して許可/不許可directory、clock/network interfaceを実行。今回WASI未実行、導入・権限は別範囲で確認|[WASI仕様repository](https://github.com/WebAssembly/WASI)、[WASI introduction](https://wasi.dev/)|
|E3|Component/WIT/canonical ABI/合成/ownership：string/list/resultの言語間往復は？|2言語componentを合成し、解放・エラー・文字列境界を実rawへ記録。今回Component/WIT未実行|[Component Model](https://component-model.bytecodealliance.org/)|
|E4|toolchain/build/配布/互換性/debug/性能/運用：異なるengineで再現できるか？|compiler/version固定、複数Browser・Wasmtime等で同一binary、起動/資源上限/失敗復旧を比較。今回単一IABとNodeであり、全runtime互換性未実行|[Wasmtime](https://docs.wasmtime.dev/)、[JS API](https://webassembly.github.io/spec/js-api/)|

## 一次資料

- [Core binary module](https://webassembly.github.io/spec/core/binary/modules.html#binary-module)：sectionとmagic/version。
- [Core instruction typing](https://webassembly.github.io/spec/core/valid/instructions.html#valid-numeric)：operand/result型の矛盾。
- [iadd](https://webassembly.github.io/spec/core/exec/numerics.html#op-iadd)：modulo 2ᴺの加算。
- [JS API](https://webassembly.github.io/spec/js-api/#towebassemblyvalue)：JS値とWasm値、instantiateと例外の境界。

locator確認：2026-10-05。原典の説明と[実検証記録](VERIFICATION.md)を分ける。[専用Skill](skills/atlas-webassembly-wasi/SKILL.md)は既存runner/checker/UIに限定。同一Agentのroutingを独立Forward Evalとは呼ばない。
