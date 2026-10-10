# GPUの小vectorとdispatch境界

問い：7要素を4laneのworkgroupで処理すると、dispatch不足・余分lane・buffer容量に何が起きるか？ 実Browser WebGPUの小さいu32加算を独立CPU oracleと比べる有限教材です。Subject全体はincomplete。native CUDA/OpenCL/Metal/Vulkan、外部GPU、機種横断保証は未実行です。

## 学習経路

1. 前提：配列・加算・byte・関数を知る。GPU製品やdriverの導入は不要。
2. 予想：workgroup_size4、7要素、1/2/3/0 groupで全て足せるか？ bufferが1要素短いと？
3. 概念・仕組み：adapter/device、storage buffer、workgroupとglobal_invocation_id、guard、encode/submit/map、検証と資源解放を区別する。
4. 実装の正常/境界/異常：6固定条件を操作し、実readback・実marker・CPU全7要素を比較。通常2group、不足1、過剰3、zero0、短いbindingとdevice dispatch上限+1。
5. 実務判断：ceil(N/workgroupSize)とguardを併用し、未計算を正常値で隠さない。未初期化値を読む代わりにsentinelを使う。入力容量とbinding条件、queue/map同期、破棄を契約へ含める。
6. 限界：markerは実shaderが書いた分類で並列実行順/時刻のTraceではない。unguarded範囲外アクセスの結果は固定期待値にしない。小vector一致から速度優位・安全一般・全GPU分野完成を主張しない。下のE1–E4へ進む。
7. 原典→[shader](add.wgsl)→[GPU runner](experiment.mjs)→[独立CPU oracle](oracle.mjs)→[固定入力](cases.json)→[checker](check.mjs)へ戻る。

## 再現と更新

このdirectoryで既存Nodeを使用、install不要。

```sh
node verify.mjs
node check.mjs
node serve.mjs
```

serverのloopback `/`はまず安全なadapter probe（requestDeviceなし）。取得できた場合だけ`/index.html`で小computeを実行する。毎回buffer6個を破棄しdeviceもdestroyする。GPU不可時は失敗/未実行として表示、logical simulatorはGPU結果に代入しない。OS/driver/権限設定を変えない。

`verify.mjs`はNodeでlogical workgroup simulatorを実行する単体検査でありGPU実行ではない。実GPU原票はBrowser操作から採取。通常checkerは保存した実原票のread-only照合。更新のみ`node verify.mjs --record observations/未使用名`、Browser raw/画像も新規保存。新原票指定は`node check.mjs --browser observations/新Browser/raw.json --node observations/新Node/raw.json`。checker記録は明示`--record observations/未使用名`のみで、既存directoryへの上書き拒否。

Source変更後は実Browserを再取得し、旧成功/失敗原票を保持する。digest-only差替えで成功扱いにしない。CPU oracleはBigInt算術と数学的prefix範囲で、shaderのlane loopをコピーしない。simulatorは別のgroup/local loopで同じ入力を説明し、実GPUとは明示区別する。

固定A=[1..7]、B=[10,20,..70]、正解=[11,22,..77]。output9要素の末尾2はsentinel99999999。GPU marker12要素は1=計算、2=guardで停止、0=dispatchされなかった。過剰12laneでもtail2は不変。短いA24byteはlayout minBindingSize28との矛盾、上限+1はdevice.limitsとの矛盾を実validation error scopeで捕捉し、異常commandをsubmitしない。

## 次の実験：主要未制作coverage

|案|概念・問い|作る実験／未実行の範囲|公式locator|
|---|---|---|---|
|E1|並列アルゴリズム/reduction/scan/workgroup memory/barriers/atomics：競合と順序をどう証明する？|小reductionの正常・意図的競合と独立oracle、同期境界を追試。今回共有memory/barrier/atomicなし|[WGSL memory model](https://www.w3.org/TR/WGSL/#memory-model)|
|E2|layout/precision/SIMD/transfer/performance：サイズと誤差でCPU/GPUの選択は？|layout/padding、f32許容誤差、upload/compute/readbackを別計測。今回性能・f32・帯域未計測|[WGSL alignment/size](https://www.w3.org/TR/WGSL/#alignment-and-size)、[WebGPU buffers](https://www.w3.org/TR/webgpu/#buffers)|
|E3|CUDA/OpenCL/Metal/Vulkan/driver/hardware compatibility：APIが違っても同じ契約か？|固定型/入力/資源上限を異なるnative API・実機で比較。今回はBrowser WebGPUのみ、native製品未実行|[CUDA公式](https://docs.nvidia.com/cuda/cuda-programming-guide/index.html)、[OpenCL Registry](https://registry.khronos.org/OpenCL/)|
|E4|device loss/cancel/権限/運用/OOM/batch/multi-GPU：停止・更新で復旧できる？|小負荷でdevice lossと再初期化、資源上限、継続ジョブを検査。今回Cloud/multi-GPU/長負荷/復旧未実行|[WebGPU device loss](https://www.w3.org/TR/webgpu/#device-loss)|

これらは未制作案で、外部GPU課金・driver設定・新依存・権限・公開の許可を含みません。

## 原典と記録

[WebGPU dispatchWorkgroups](https://www.w3.org/TR/webgpu/#dom-gpucomputepassencoder-dispatchworkgroups)、[bind group validation](https://www.w3.org/TR/webgpu/#dom-gpudevice-createbindgroup)、[mapAsync](https://www.w3.org/TR/webgpu/#dom-gpubuffer-mapasync)、[WGSL compute](https://www.w3.org/TR/WGSL/#compute-shader-stage)、[out-of-bounds](https://www.w3.org/TR/WGSL/#out-of-bounds-access)。2026-10-05に公式資料を確認。WebGPU全本文は取得量上限で取得失敗、関連公式検索抜粋とWGSL本文を参照し、仕様全体を消化したとは主張しない。

実観測は[検証記録](VERIFICATION.md)と原票で示す。[専用Skill](skills/atlas-gpu-computing/SKILL.md)は既存runner/UIへ限定route。同一Agent routeは独立Forward Evalではない。自作中立vector、転載素材なし。
