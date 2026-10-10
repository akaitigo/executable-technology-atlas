# Atlas：サンプル時刻の原典と既存教材

## 原典を読んで確認したこと

[RFC3550 §5.1](https://www.rfc-editor.org/rfc/rfc3550#section-5.1) の timestamp の説明を正式な web 読取で確認しました。サンプリング時点と、ペイロードに応じた時計の周波数が基礎です。周期的なデータでは、処理した瞬間のシステム時刻をそのままサンプル時刻にしません。異なるストリームの時刻は基準や速さが異なるため、数値を直接比べるだけでは同期になりません。

今回の読取位置は RFC の timestamp 説明、取得表示の825–873行です。web の解析テキストを読んだ記録であり、raw本文のバイト列を保存したことや、そのハッシュを取得したことは主張しません。取得エラーや再試行はありません。

この教材の48000 sample/s、整数ms、原点0、0.5を上へ丸める規則、+100ppm は比較のために固定した独自条件です。RFC が要求する数値ではありません。RTPヘッダー、パケット、到着時刻、32bit wrap、RTCP の時刻対応を実装した教材ではありません。

## 既存の不足との対応

分野目標は `task-8/atlas-97-field-goals-ja.md` の94番、1088–1097行を読取りました。既存の目標は、固定した時計差と時刻単位の換算を有理数の時系列で比べ、丸めと累積誤差を照合することです。

元教材は `executable-technology-atlas/learning/subjects/media-codec-streaming/README.md` と `coverage.json` の `timebase-drift`。既存の mono16/8kHz、80サンプル=10ms、4区間のPTS・到着順比較を確認しました。整数msの既存比較に対して、今回の問いは非整数換算と丸めの積み重ねです。

`learning/continuations/media-codec-streaming/riff-chunk-padding/` はRIFFのチャンク長・padding・バイト境界を扱います。再生時計を測っていない範囲も確認し、今回の換算と区別しました。

`learning/continuations/game-engine-interactive-simulation/fixed-tick-render-interpolation/README.md` は固定tickと描画補間の比較です。共通する時刻の基礎を新しい成果として数えず、今回のサンプル単位→整数msと時計倍率の差に限定します。同pathのCOVERAGE.mdは指定名で見つからなかったため、READMEで確認しました。ファイルが見つからないことを分野の不存在とは扱いません。

上記は指定された既存経路と索引での確認です。PC全体に同種教材が一切ないという主張ではありません。元の分野担当の現在状態は未確認で、共有元や台帳へ書き込みません。
