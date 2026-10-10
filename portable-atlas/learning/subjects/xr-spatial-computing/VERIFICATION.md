# 検証記録

有限unitを実CPU/Browserで実行しました。Subjectは **incomplete**。XR session・device・tracking・depth計測・実空間安全、全体Goalを検証していません。

## 現行原票

- [Node](observations/node-attempt-02/raw.json)：2026-10-05T09:16:59.017Z〜09:16:59.022Z。Node v25.2.1 / V8 14.1.146.11-node.14、darwin arm64。13入力、2,351比較assertion。4×4積/Gauss–Jordanを実CPU実行し、独立成分式・厳密right-angle table・rational handcaseを照合。
- [Browser QA](observations/browser-attempt-02/raw.json)：09:17:56.357Z〜09:18:15.984Z。Chrome/154.0.0.0というUA、language ja、1280×720、DPR 2。9操作記録（全13入力、degree/radian/誤用/45°/拒否、keyboard実行）。実行時刻・環境・input・raw matrix/inverse/world/back/axes・図geometry・表・answer表示・実Screenshotを保持。
- [checker](observations/check-attempt-02/raw.json)：6,727 positive比較assertion、11改ざん負例を拒否。negative中の失敗地点までの20,604比較は別計上で、成功件数には加えない。
- [Source集合](sources.mjs)13 memberはchecker/Skillも含む。[check.mjs](check.mjs)がSource全hash、input digest、Node/Browser artifact digest、Screenshot hash、rawTextとparsed raw、全数値、投影geometry、UI表/状態、学習経路を照合する。

90°入力のworldはT×R=(1,3,2)、R×T=(2,3,−3)。両方のroundtrip誤差は今回2.22e-16。π/2をdegreeとした誤用のworldはTR=(2.972212,3,1.972964)表示だが、roundtripは2.22e-16で通る。角度単位の意味を逆変換だけでは検証できない反例を実行した。

raw許容差1e-10、図1e-8 SVG pxは実行前に固定。geometryは独立oracleで得たworld/parent axisを同じ明示射影へ写したものと比較。原票の残差は丸めず、画面は6桁表示。数値precision・図はXR API/Float32/tracking/stereo精度の証拠ではない。

![変換順序の実Browser画面](observations/browser-attempt-02/normal-degree.jpg)

## 初回・失敗の保持とSkill

[初回Node](observations/node-attempt-01/raw.json)・[初回Browser](observations/browser-attempt-01/raw.json)・[初回checker](observations/check-attempt-01/raw.json)を保持。90°図のlocal軸ラベルが重なっていたため色凡例へ修正し、変更後SourceのNode/Browserを別directoryへ実再実行した。旧原票は当時Sourceの履歴であり、現行Sourceのpassへ流用しない。

[通常preview拒否](observations/preview-default-denied/raw.json)：個別exit1、listen EPERM/127.0.0.1。toolに個別開始/完了時刻がないためnull。pathを含むstackを保存せずerror excerptを保存した。その後、同じ教材の一時loopback待受をホスト審査で起動した。恒久設定・外部公開なし。

quick_validateはexit0 / `Skill is valid!`。同一agentのsupported routeはnormal-degreeとrunにfocusしてEnter。unsupportedな実tracking精度・実空間安全要求は未制作E2/E4へ案内、XR session/sensorは起動しない。このroutingは独立Forward Evalではない。

## 原票保護と終了

通常の `node verify.mjs` / `node check.mjs` はread-only。記録は明示 `--record observations/NEW-ID` に限り、新directoryを作成する。既存directoryへの記録拒否と、通常検証前後のfile hash不変を `observations/read-only-audit/raw.json` へ保存する。report自身は自己hash循環を避けるため集合から除外する。

教材専用tab16を閉じ、Node sessions59944/50512をSIGINTで終了（exit130）。ports64014/64427のlsof LISTEN確認はexit1・出力0、待受なし。新依存・Docker・課金・device権限・OS/GitHub設定・commit/push/公開・新Goalなし。専用moduleだけを編集し、他writerのroot/他Subject差分には触れていない。Root/Core全Gate未実行であり、有限unitのpassをSubject/Repository完成へ拡張しない。
