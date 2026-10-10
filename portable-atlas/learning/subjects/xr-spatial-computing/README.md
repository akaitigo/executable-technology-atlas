# localからworldへ：座標変換の順序

回転・移動したparent frame内のlocal点をworldへ変換し、T×RとR×Tの違い、逆行列、角度単位の誤用を実CPU/Browserで比較する有限教材です。Subjectは **incomplete**。XR API・機器・tracking・depth・実空間安全の実証ではありません。

## 学習の道筋：前提 → 概念 → 操作

前提は3成分座標、degree/radian、行列と列ベクトルです。worldとlocalを別のframeと考え、同じ点でも所属frameが違えば値が違うことを学びます。

1. `node serve.mjs` を実行し、表示された動的127.0.0.1 URLを開く。確認後はCtrl+Cで停止する。
2. local(1,2,−1)、translation(2,1,3)、Y軸＋90°のworld点を予想する。
3. normal-degreeを操作し、T×RとR×Tの座標・parent原点・local軸を比較する。
4. normal-radian、radians-as-degrees、45°、0/−90/180/360°、拒否入力を比較し、答えを開く。
5. [入力](cases.json)、[通常・拒否の実装](model.mjs)、[独立oracle](oracle.mjs)、raw matrixを見る。

## 固定した座標規約と仕組み

- 列ベクトル、`world=M*local`。右側の変換から適用する。
- 右手系：＋X右、＋Y上、＋Z手前、X×Y=Z。＋Y回転は＋Xを−Zへ回す。
- `Ry(θ)` の成分は `(x,y,z) → (cosθ*x+sinθ*z, y, −sinθ*x+cosθ*z)`。Y軸だけの剛体変換で、scale/shearは扱わない。
- raw matrixRowsは行別nested array。matrixColumnMajorは同じ行列をcolumn-major16値へ並べたJS Number配列。WebXR Float32ArrayやXRRigidTransformを呼び出した結果ではない。
- pointはw=1。位置の単位は名目上mの合成sceneで、校正値やdevice測定値ではない。
- degreesは `angle*pi/180`、radiansは値を直接使う。教材では絶対角度≤360°/2π rad、座標絶対値≤5を事前検証。上限は教材契約であり数学上の制限ではない。w=0の方向vectorも別の意味としてこのpoint入力から拒否する。
- 説明図は `u=x−z/2, v=−y+z/4` の線形斜投影。両panel同じscale、原点は185/555,160、SVG yは下向き。perspective/左右眼/depth推定ではない。表示は6桁に丸めるが原票は丸めない。

通常実装は汎用4×4積とGauss–Jordan逆行列を実行します。独立oracleはruntime関数をimportせず、成分式と剛体逆変換 `Rᵀ(world−t)`、およびRT逆の `Rᵀworld−t` で照合します。0/±90/180/360°はsin/cosの厳密な整数table、45°と角度誤用は浮動小数点です。rational座標のright-angle handcaseも別に固定しています。

実行前に固定した許容差はraw数値の絶対誤差 **1e-10**、説明図geometryは **1e-8 SVG px**。全matrix/inverse/identity product/world/back/origin/axes/projectionを比較し、入力・flag・IDは厳密一致します。roundtrip残差は0へ補正せず保存します。一般のsingular行列や悪条件の逆行列は検証していません。

## 正常・境界・意図的異常から何を判断するか

| 入力 | T×R world | R×T world | 学ぶこと |
|---|---|---|---|
| Y＋90°、t=(2,1,3)、p=(1,2,−1) | (1,3,2) | (2,3,−3) | 移動vectorも回る順序反例 |
| π/2 radians | 上と同じ | 上と同じ | 単位を変換して一致させる |
| 回転0° | (3,3,2) | (3,3,2) | この条件では順序差が現れない |
| π/2をdegreesで渡す | 90°の結果と異なる | 90°の結果と異なる | 値がvalidでも意図は間違い得る |
| 非数値角度／上限超過／w=0／grad | 計算前拒否 | 計算前拒否 | finite lessonの入力境界 |

両順序の行列はどちらも可逆で、角度単位の誤用も自身の逆行列でlocalへ戻ります。したがってroundtripだけで「期待したframe・角単位・配置だった」とは判断できません。外部APIを繋ぐ時は所属frame、単位、vector規約、matrix storageを独立に確認する、という判断をこの教材から得られます。

## 次の主要未教材Coverage

具体的な問い・範囲・実験とprimary locatorを[scope.json](scope.json)へ対応付けました。全て未制作、機器や権限の取得は別の作業です。

- E1 quaternion／任意軸／rigidとaffine／階層frame：実XRRigidTransform・DOMMatrixとの相互変換、zero quaternion、singular scaleを比較する。[WebXR §8.1–8.3](https://www.w3.org/TR/2026/CRD-webxr-20260609/)、[Geometry Interfaces §6](https://www.w3.org/TR/geometry-1/)
- E2 tracking／6DoF・SLAM／space reset／pose loss・drift／hit test・anchor・depth：実機でrecenterや喪失を観測し、同一frameの情報を保存する。[WebXR §5/6/9/12](https://www.w3.org/TR/2026/CRD-webxr-20260609/)、[Hit Test](https://www.w3.org/TR/webxr-hit-test-1/)、[Depth Sensing](https://www.w3.org/TR/webxr-depth-sensing-1/)
- E3 stereo／render・occlusion／scene・assets・audio／controller・hand・gaze・haptic／latency：実左右viewとinput rayを比較し、budget超過・lifecycleを注入する。[WebXR §4.4/7/10/11](https://www.w3.org/TR/2026/CRD-webxr-20260609/)
- E4 実空間安全・comfort／privacy・consent／multimodal accessibility／session復帰／operations・機種互換：拒否・終了・復帰と代替入力を機種別に確認し、利用者・実空間レビューを別Evidenceにする。[WebXR §13/14](https://www.w3.org/TR/2026/CRD-webxr-20260609/)、[XR Accessibility §4](https://www.w3.org/TR/xaur/)

## 原典・権利・再現

参照したWebXRは2026-06-09のCandidate Recommendation Draftです。§8.1の列ベクトルとcolumn-major、§8.3の回転後移動・逆変換は概念の入口ですが、今回はquaternion/API/deviceを実行していません。[公式原典](https://www.w3.org/TR/2026/CRD-webxr-20260609/)と独自toy実装を分けてください。実装・説明図は独自、外部画像・測定素材・依存追加なし。

```sh
node verify.mjs
node check.mjs
```

通常はread-only。原票を新規保存する時だけ `node verify.mjs --record observations/NEW-ID` / `node check.mjs --record observations/NEW-CHECK`。既存directoryをEEXISTで拒否します。Browserは通常UIを操作してraw文字列と実screenshotを保存し、source/artifact digest・時刻・環境を固定します。checkerに別原票を渡すなら `--node observations/NEW-ID/raw.json --browser observations/NEW-BROWSER/raw.json`。

[検証記録](VERIFICATION.md)、[有限routing Skill](skills/atlas-xr-spatial-computing/SKILL.md)。同一agentのSkill試験は独立Forward Evalではありません。このunitのpassからSubject/全体Goal完成を推定しません。
