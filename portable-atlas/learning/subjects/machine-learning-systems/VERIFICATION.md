# 検証記録

問い：model artifactが期待するfeatureの意味を入力が保っているか。経路：Mac直接Python標準ライブラリ→固定JSON modelと入力→strict/naive trace→loopback HTTP→IAB。

モデル係数は手動固定、訓練は行っていない。11requestの正常/契約不一致/境界、6種類の追加拒否、100個のseed固定入力と交換、batch拒否と6種類のartifact拒否、独立named Fraction/schema/stat oracleを照合する。通常checkerはread-only、原票更新は明示 --record のみ。作者routing smokeは独立AgentEvalではない。

実行時刻・環境とmodel/input/source/artifact digestはobservations/receipt.jsonへ保存する。UIはraw traceの説明用再生でありライブ推論ではない。実IAB QA、capture保存可否、ownedserver/tab終了はobservations/ui-qa.jsonへ保存する。

全Subject完成、実ML/LLM、実MLOps service、drift検出や精度低下判定、外部API、Docker、本番配信は未実装/未検証。指定外path、Portal/Core、Goal、commit/pushは変更しない。依頼の範囲に従い全体gate/full verifyは未実行であり、module通過を全体成功へ拡張しない。

## 実観測 — 2026-10-05 JST

Python 3.9.6 / Darwin arm64。11request×strict/naive、100個の固定seed正常入力と交換、追加値拒否6種類、batch拒否3種類、artifact拒否6種類を通過。正常11、同意味の順序交換のnaive18.5とstrict拒否、零境界1、最大境界251を独立手計算と比較。未知versionはstrict拒否、naiveの11は意味未定義として扱った。巨大整数をfloatへcastせず域外で拒否する境界も検査した。

reference/new_inputは4行ずつ、hours平均2.5/11.5・母std1.118033988749895、tasks平均5/5・母std2.23606797749979、score平均8.5/26.5・母std3.3541019662496847。rational sumによる独立統計oracleと一致。検出器・検定・精度低下判定の証拠ではない。

Skill quick_validate通過。正常schemaと未対応production-deployの作者routing smokeを実行。Node vm.ScriptによるUI構文検査は通過したがブラウザ実行とは別に記録する。通常checkerはplain python3でもmodule全ファイルの前後SHA-256一覧が不変で、bytecodeを書き込まなかった。原票更新は明示 --record だけ。

## loopback・実IAB・cleanup



startupの実port51300でHTTP接続し、title、case/policy select、step range、buttonsを確認。22結果を実IABで操作してtrace DOMを読み、独立期待と照合。追加の境界強化後はrawを再読み込みし、同じ22結果を再照合した。ui-matrix.jsonは実locator出力の転記で、checkerが期待値から生成したブラウザ結果ではない。UIで観測したraw digestもQAに保存し、通常checkerが現rawとの一致を確認する。

traceの契約段・積和段、model/input hash、統計6行と元batch/推論列、記述統計だけという注記、原典locator、主要9領域coverageと次の4実験を確認。実captureを4回ツール出力で目視。画像ファイルはrepoへ保存せずlocal pathと画像digestはない。再描画も行っていない。desktopの表示範囲で日本語と表・traceに重なりを認めなかった。mobile viewportは未確認。

owned IAB tab3をcloseし、serverをCtrl-Cで終了、exit0を確認。HTTP logはpreview-http.logに保存。favicon404も維持し、教材JSONの初回取得と最終raw取得は200。全体Core/Portal gateは未実行。Scopeはこの有限教材のみで、Subject全体完成にはしない。
