# 検証記録

確認日2026-10-05 JST。7要素の固定vectorを実Browser WebGPUで駆動した有限教材。Subject全体と旧Goalは未完了。新Goalなし。Portal root Gate/Core auditは今回未実行、旧repo/root文書/他教材は変更していない。

## 安全probe→実compute

- [初回adapter原票](observations/probe-attempt-01/raw.json)：08:13:34.032–08:13:34.059 UTC、navigator.gpu=true、requestAdapter成功。adapterの報告値はapple / metal-3、fallback=false。device取得・shader実行はこのprobeではしていない。
- 初回probeのSource集合は4 memberの旧時点で保持。SOURCESを15 memberへ追加した後、旧原票のhashを推測追記せず[最終Source probe](observations/probe-attempt-02/raw.json)を08:25:19.571–08:25:19.579 UTCに実再取得。同じadapter成功、device/compute未実行。これにより古いprobeを最新Source実証へ読み替えない。
- [最初のcompute原票](observations/compute-smoke-01/raw.json)：08:22:43.013–08:22:43.211 UTC、正常7出力を確認し実画像も保存。
- [本QA原票](observations/browser-attempt-01/raw.json)：08:23:53.386–08:23:58.843 UTC、UA Chrome154.0.0.0 / Mac OS X10_15_7 / ja / secureContext / 1280×720。UAは実record値で実OSの独立probeではない。8操作で全6条件を実行し、raw文字列・構造化raw・table cell・snapshot・JPEGを別保存。
- [Node原票](observations/node-attempt-01/raw.json)：Node25.2.1 / V8 14.1.146.11-node.14 / darwin / arm64、08:21:59.509–08:21:59.514 UTC。logical simulatorの10照合でありGPU実行ではない。GPU validation2条件はsimulatorで閉じずrequires-real-gpuと記録。
- [checker原票](observations/checker-attempt-01/raw.json)：08:24:10.301–08:24:10.324 UTC。536肯定照合、9負例拒否、負例の失敗前照合774は別集計。Source/Input/Shader・実readback・marker・table cell・例外・解放・実JPEG hashを確認。

GPU buffer/deviceは各case専用に作成。sourceで指定する6buffer計240byte（異常短binding時236byte）、全6bufferをdestroyしdeviceもdestroyした記録を全caseで照合。pipeline内部資源やdriverメモリ全体の消費量を測定したとは主張しない。

## 観測

|条件|実readback / marker / 拒否|
|---|---|
|2group×4lane|7要素=[11,22,33,44,55,66,77]、guard marker1件、末尾2sentinel不変|
|1group×4lane|4要素だけ計算、残3はsentinel。markerの残8は0|
|3group×4lane|7要素計算、余分5lane marker2、末尾2sentinel不変|
|0group|submit/mapは実行、shader invocationは0。全出力sentinel・全marker0|
|A24byte < layout min28byte|CreateBindGroupで実GPUValidationError。submit/mapなし|
|dispatch65536 > device limit65535|DispatchWorkgroups/finishの実GPUValidationError。異常commandはsubmitせず|

markerはshaderがstorage bufferへ実際に書いたもの。parallel順序/時刻ではない。unguarded範囲外アクセスの不定な返値は実行もoracle化もしていない。CPU oracleはBigInt exact算術＋prefix範囲、GPU runnerへ期待値を代入しない。実GPU kindとsimulator kindは別。

9負例：GPU→simulatorへの偽装、tail書換、不足dispatchを埋める捏造、guard marker欠落、validation class混同、resource漏れ、stale shader/source、条件欠落、時刻欠落。cloneだけを変更し、実成功/拒否原票を保持。

## Digest・Skill・未達

|実体|SHA-256|
|---|---|
|cases.json|f871ab842d0495db1953c4d6b5f3fa9f6c03ac001e7200616cf0da3b840c45cc|
|add.wgsl|47563d145050284e31c9ca972aa7c4dd18bb00b5ffb7c99f1f6fdd6caba72dfe|
|Browser raw|a2f60725567e04ba14e84abc7c693c5c95d8b8166a1ee03ad0d54d5559803703|
|Node simulator raw|99778ae703e7b0a859f239f13ce3e02679fe14f5130b58b8e7bc67b856fb9d0d|
|初回probe JPEG|c9c3e41770fd0a2adbca6a02a28377abf2bbe93af065a5db10aafd103b581126|
|最終probe JPEG|45303bbbc8aad420a1f06f994649c671e7b4d7673acd9729256b5b0c7a5d8a0f|
|Browser/adapter/limits identity JSON|56a3c4fd94ed9e4e0cae41a65667194b67cb08c5479ab6e29d75e1d80d850346|

各case入力はfixture＋caseのJSON.stringifyをUTF-8 SHA-256化、shaderは実読込文字列のUTF-8 hash。identityは最初の本QA rawから{environment,adapterInfo,limits}のキー順でJSON.stringifyしてhashした派生識別子、driver binary hashではない。Source集合は15 member固定、probe/GPU runner/shader/oracle/checker/UI/Skillを含む。README/事後検証文書は説明なのでSource集合の外だが通常検査前後の全ファイル不変監査に含める。hashは実行内容の同一性識別でありGPU安全/性能一般の証明ではない。

Skill quick_validate成功、正常routeは同一Agentがnormalを選びEnter、実GPU output/markerを比較。CUDA install/Cloud課金/速度保証routeは未対応としてE2/E3/E4へ案内、何も導入・契約しない。同一Agent routingは独立Forward Evalではない。

CUDA/OpenCL/native Metal/Vulkan、他製品/driver/端末、Cloud/multi-GPU、f32精度・帯域・速度比較、reduction/atomics/barrier、device loss復旧と長負荷は未実行。scope.json、README/indexのE1–E4へ具体的に接続する。GPUがない別環境では失敗原票とlogical simulatorを区別し、この環境の成功を転用しない。

own tab14終了、own server session14715/76737をCtrl+C exit130。ports58431/59402のlistenerはlsof0件/exit1。OS/driver/GitHub設定、新依存、外部課金、新権限の永続付与、Docker、commit/push/公開なし。最後にread-only verify/check/Skill検査・既存record拒否・全ファイルhash不変・private path/既知secret pattern scanをobservations/read-only-audit-01へ記録する。
