# Token / button教材の検証記録

問い：instance overrideの所有範囲、不正色のfallback境界、themeとnative disabled/keyboardを比較できるか。独立oracleはCSS/APIをimportせず固定computed token表と13状態を持ちます。Nodeはpure APIのみ、Browser原票照合は実CSS/DOM/属性/入力eventを検査します。

## 実QAと経路

2026-10-05 15:51:44.821–15:52:38.186 JSTに背景IABで実操作した[Browser原票](observations/browser-attempt-01/browser.json)を保存。環境は実BrowserがDOMへ記録したUA `Chrome/154.0.0.0` / Macintosh、ja、1280×720。UA表記でありbinary versionを別検査した値ではありません。13状態それぞれの実computed style、DOM属性、focus、入力eventのbefore/after/outcome/時刻、DOM snapshot、配信Source10ファイルのhashを保持します。Browser測定と教材のdomain instrumentationを分け、OS/全Network traceとは呼びません。

初期→dark→light→A上書き→not-a-color→上書き削除→disabled→Tabでbug-aをskip→Tabでsafe-aをskip→enabled→Enter→Space→resetを操作。左のBまでmagentaが漏れ、右のBはblueを保持。不正色は左のbackground-colorがrgba透明、右はテーマのblue。disabledのAには実属性が付き、Tab先はそれぞれB、Enter/Spaceは局所版Aのcounterが0→1→2となりました。予想only-aと3回答のfeedback、展開した学習案4rowも採取しています。

[現在SourceのNode原票](observations/node-attempt-02/node.json)は15:50:39.722–15:50:39.725 JST、Node v25.2.1/darwin/arm64、13状態・63項目成功。pure APIでありCSS engine証拠ではありません。[独立checker原票](observations/check-attempt-01/check.json)は15:52:47.790 JST、保存Browserの13状態・307項目成功。漏れ隠蔽、架空の不正色fallback、safe sibling漏れ、disabled属性欠落、disabledへfocus、keyboard入力欠落、偽Sourceの7改変負例を拒否。合成改変を実Browserでそのバグを起こした証拠とは扱いません。README/indexの8未教材→4案、local link16件、現Source bindingも確認しました。

## 原票と実画面のdigest

| 成果物 | SHA-256 |
|---|---|
| Browser原票 | `dfb15815befff67776ca294b1cce62a7f954aabbd6b6b3f0bb1d2fb8df953d8b` |
| Node原票（attempt-02） | `968de4f8d4c6bebe769497eaf88c020734bea116506f7a081794ee657952610a` |
| checker原票 | `9c2a847b25ae154ecd07499beb261b26f7d06a775ffbfd79226b090f90fda8d2` |
| [読み取れる漏れ比較画面](observations/browser-attempt-01/leak-visible.jpg) | `51a36e2bda79dc428c722b8d89d7442d11eb04c8b1789ad7ff4ad68e14796141` |
| [不正色の画面](observations/browser-attempt-01/invalid.jpg) | `793af6a31e0bf63347de2212972be043b39e13d0d2a573af2fdcfcf2ee150fbe` |
| [disabled・Tab focus画面](observations/browser-attempt-01/disabled-keyboard.jpg) | `5e29eb827f6b0c813801891b496bd6bc59adbf3021917b4773140e526cbdc23f` |
| [未教材roadmap画面](observations/browser-attempt-01/roadmap.jpg) | `9f02d1aa26b5c9eaccbb2e47e19ac5e4a7f68b6b134822617018e8960128840f` |
| [所有図の実表示](observations/browser-attempt-01/scope-diagram.jpg) | `0606a68f3127f9590e9e4a76b59c09eeb3f32b2d9de24272ab326b8ff6dbf0e3` |
| [同一Agent Skill確認](observations/skill-control.json) | `13ec95bdcc8fd42ee6ff2ebba184640349e327f95977fa4d081757fa773f852a` |

全7画像は無加工JPEG、実viewport1280×720。初回[leak.jpg](observations/browser-attempt-01/leak.jpg)は操作欄中心でmetricsの下が見切れたため保持し、同じ実装をSkill通常routeで再操作してvisible画像を追加。invalid画像も下部metricsは見切れ、透明なbutton labelは読めなくなる意図異常ですが、値は原票の独立DOM/CSS検査で確認。長いroadmapは一枚に収まらず全4rowはDOM snapshotで確認。scope図は独自の説明図を実表示した画面でありCSS engine traceではありません。[初期画面](observations/browser-attempt-01/initial.jpg)の保存成功も確認しました。

## 失敗保持・read-only・Skill・cleanup

[listen失敗](observations/listen-failure-01.json)は通常sandboxの一時loopback listenがEPERM/exit1。指示で認められた一時loopbackのみホスト審査を利用し、OS設定/永続権限を変更していません。

[環境情報のread失敗](observations/environment-read-failure-01.json)はCua DOM evaluatorでnavigatorを参照できずTypeError。アプリ自身が実UA/viewportをDOM原票へ記録するようSource修正しました。修正前の[Node attempt-01](observations/node-attempt-01/node.json)は削除せず歴史的証拠として保持し、現在Sourceの成功には使用しません。修正後Node attempt-02とBrowserを実再実行。取得変数の初期化漏れ[ReferenceError](observations/record-init-failure-01.json)も採取前の失敗として保持します。既存原票への推測追記はしていません。

15:53:56.954 JSTに通常verify/checkはexit0。既存node-attempt-02/check-attempt-01への明示recordはexit1/EEXISTで拒否され、前後で教材内27ファイルの全hash不変を確認。これは当時のファイル集合で、後の検証文書追記は別の編集です。

専用Skillのquick_validateは成功。同一Agentの通常routeはreset状態からA背景を適用し、左のBにも漏れ/右のBはtheme保持を実UIで確認。未対応の実配布/全design system/WCAG保証はE1–E4の学習案へ案内し、保証falseと記録。独立Forward Evalは未実施です。スキル方針に従い、実測・合成改変・次案を混同せず整理しました。

own tab10を終了。最初のown server127.0.0.1:52024と再取得のown server127.0.0.1:52242はCtrl+Cで停止（exit130）。両portのlsof listener検査は出力なし/exit1。他taskのtab/processへ触れていません。

変更は専用directoryだけ。Portal root README/docs、Core/Graph、旧FE repo/Goal、他Subjectは変更していません。Docker/新依存/外部サービス/新永続権限/OS・GitHub設定/global Skill install/commit/push/公開/新Goalはありません。Portal全体Gate/Core auditは未実行であり、この有限1教材をSubject全体または全体Goalの完成とは扱いません。主要8未教材coverage→4案は将来計画で、実配布/複数Browser/全design system/全アクセシビリティ適合は未実証です。
