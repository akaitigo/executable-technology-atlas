---
name: atlas-gpu-computing
description: 既存の小vector教材を実Browser WebGPU・CPU oracle・read-only checkerで学び、dispatch不足/guard/validation境界を比較する。GPU不可時は明示simulatorに限定し、CUDA/外部GPUや性能保証には使わない。
---

# 7要素の並列計算へ案内する

module rootはこのSkillから`../../`。README/scope.jsonを読む。まず`node serve.mjs`のprobeでnavigator.gpu/requestAdapterを確認。不可なら失敗原票を保持し、simulatorをGPU成功と呼ばない。driver設定・外部GPU・課金を行わない。

対応routeは「dispatch不足/余分laneとguardを見たい」。既存index.htmlで予想→固定条件→実GPU readback/markerとCPU比較→shader/runner/oracle/原典→答え。normalを選択してEnter、2group×4laneで7計算＋1guard、末尾2sentinelとbuffer解放を確認する。markerは実結果だが並列順序Traceではない。unguarded範囲外の不定な結果を固定期待値にしない。

`node verify.mjs`はlogical simulatorの単体検査、GPU実行ではない。`node check.mjs`は保存実Browser原票のread-only検証。更新だけ明示`--record observations/未使用名`で、Browser raw/画像も新規保存。Source変更時は実Browserを再取得し、hash差替えだけで通さない。owned tab/serverだけ終了、GPU buffer/deviceもrunnerで破棄する。

未対応route「CUDAをinstallしてCloud GPUを契約し速度保証」はREADME E2/E3/E4へ案内し、この教材では未実行・権限/費用なしと伝える。全GPU分野完成や機種横断保証をしない。同一Agent route確認は独立Forward Evalではない。
