# vec3配列strideとpadding

元[GPU Subject](../../../subjects/gpu-computing/README.md)のE2 layout未教材を追加する。既存u32加算/dispatch境界やHPC reductionは繰り返さない。[UI](index.html)で予想→CPU配置→実GPU→正常/故障/validation→一次資料/source/実raw→答えへ進む。

## byte配置の契約

WGSLの `array<vec3<f32>,2>` はvec3 size12・alignment16、array stride16、全体32byte。CPUも32byteを確保し、未使用wordを99で埋める。

| CPU pack | byte0/4/8/12/16/20/24/28のf32 | WGSL実read offset0/4/8/16/20/24 |
|---|---|---|
| stride16 | 1,2,3,99,4,5,6,99 | 1,2,3,4,5,6 |
| 故障stride12 | 1,2,3,4,5,6,99,99 | 1,2,3,5,6,99 |

GPUへのbindingはどちらも32byteでvalid。stride12の内容不一致はvalidation errorにはならない。第二vec3末尾6/8、padding99/-1、stride12/16の有限入力を実GPUへ通す。32byte配置図は実upload bytesの説明であり、CPU計算をGPU結果に代入しない。

[shader](shader.wgsl)が2つのvec3を実読取し、bitcastした6u32をscalar arrayへ書く。24byteをGPU copy→mapAsyncし、u32 bitsとf32をreadback。buffer3つをdestroy、deviceもdestroy。時刻はBrowser実UTC、runtimeは実user agentで、並列Trace/性能測定ではない。固定正確整数f32だけで丸め誤差一般は未検証。

binding28 fixtureは実32byte bufferのbinding sizeだけ28にし、minBindingSize32との矛盾を実GPUValidationError scopeで捕捉してcomputeをsubmitしない。adapter/device/driver失敗時はGPU_UNAVAILABLEまたはGPU_EXECUTION_FAILURE、GPU readbackなしと明示する。CPUでGPU成功を代用しない。shaderのHTTP取得失敗もGPU_EXECUTION_FAILUREとして別記録し、通常答えを空にする。

## 再現と証拠

```sh
python3 -B verify.py
python3 -B route.py
python3 -B serve.py
```

既存Python標準ライブラリ、既存Browser WebGPUのみ。server表示の127.0.0.1一時portを開く。adapterだけprobeはrequestDeviceしない。実実行を押して小computeする。所有serverだけCtrl-Cで終了。install・OS/driver/Docker/権限設定変更なし。

通常checker/routeは保存した実GPU原票の読み取り専用照合で、GPU再実行ではない。GPU再実行はUI操作で明示し、未使用新原票に保存する。[事前手表](hand-oracle.json)のliteral offset/LE hex/u32 bitpattern/最終値を[独立oracle](oracle.py)で照合する。producerのpackやshaderをsolverとして再利用しない。6mutantが誤readback/bits/offset/hex、validation成功偽装、未破棄を拒否。

制作時は既存Apple/Metal-3 adapterで実compute/readback。原票・source/artifact digest・環境・実UI QA・capture保存可否をobservationsへ保存する。初回checker記録は `python3 -B verify.py --record attempt-01`、UI確定後sealを一度。既存成功/失敗原票を上書きしない。[Skill](skills/vec3-stride/SKILL.md)はこの単元だけへのrouteで、独立Agent評価ではない。

## 原典と未教材

[WGSL Candidate Recommendation Draft 2026-09-21 / Alignment and Size](https://www.w3.org/TR/2026/CRD-WGSL-20260921/#alignment-and-size)とArray Layout Examplesはvec3 alignment16・size12およびroundUpによるarray stride16を説明する。制作時に公式本文を直接取得して確認。

未教材: struct/uniform/dynamic offset、f16/NaN/丸め誤差、SIMD、転送帯域・速度、native CUDA/Metal API、driver横断、device loss復旧、multi-GPU、実サービス安全性。次はstruct member配置とuniform制約を別原票で追試する。Original97/Core/Portal/共有docsは変更しない。Core/full gateは専有範囲外で未実行、GPU分野/Atlas全体の完成は主張しない。

追加のstride0入力拒否fixtureは別事前手表input-refusal-hand.jsonで固定し、buffer構築・adapter/device取得前のREFUSED_INPUTを実UIで確認する。これはGPU validationやGPU成功とは別扱い。

予想変更もticketを進め、実result/raw/readback/32byte配置図/回答を消し、新しい予想は保持する。保留した旧応答は採用しない。改修前30fileはprediction-reset-historyへmtime/hash付きで保存し、中央指摘と改修QAを追記。旧GPU原票・旧UI QAは変更しない。
