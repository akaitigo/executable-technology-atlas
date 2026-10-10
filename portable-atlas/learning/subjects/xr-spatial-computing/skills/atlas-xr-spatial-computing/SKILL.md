---
name: atlas-xr-spatial-computing
description: 合成sceneのparent/local/world座標、T×RとR×T、逆変換、degree/radianを既存CPU/Browser教材で比較する。XR deviceやtracking、安全評価には使わない。
---

教材rootのREADME.mdを読み、既存cases.json/model.mjs/oracle.mjs/UIを使う。列ベクトル・右手系・Y軸回転・w=1のpoint・説明用斜投影を保持する。

- 予想→normal-degree選択→「選択入力を計算」→normal-radianとradians-as-degrees比較→答えへ案内する。runへfocusしてEnterでkeyboard実行できる。
- `node verify.mjs` / `node check.mjs` は読み取り。新しい原票だけ `--record observations/NEW-ID`。既存directoryへ書かない。serve.mjsの動的localhostと通常UIを使い、所有tab/serverだけ終了する。
- roundtripが通っても角単位・frame・座標規約の正しさは保証しない。rawはJS NumberのCPU計算、図は3D値の斜投影でありtracking/実depth/左右眼renderではない。
- quaternion/実APIはE1、device/pose/SLAM/depthはE2、stereo/input/render/latencyはE3、privacy/実空間安全/accessibility/復帰はE4へscope.jsonの未制作経路を案内する。今回はXR session・sensor起動や依存/権限追加へ進まない。
- 同一agent routingは独立Forward Evalではない。有限unitのpassをSubject/Goal完成へ拡張しない。
