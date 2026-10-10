# Atlas：上位値で隠れる不正設定

timeoutの上位値が3000なら、下位の"oops"を放置してよいでしょうか。型検査を合成の前にするか後にするかで、何が検査され、何が残るかを比べます。

[前提](PREREQUISITES.md) → [予想と操作画面](index.html) → [手追跡](HAND_TRACE.md) → [原典・実装](reference.html) → [Skillの6問](SKILL.md)へ。現在の実施状態は[status](status.json)、計算と画面の証拠は別に記録します。

6入力を2方針で比較します。全層検証は各値を先に検査してから合成し、勝者だけの検証はrawを合成してから4勝者を検査します。両方とも未知field等の構造検査を最初に行い、拒否時config/provenanceはnullです。診断の候補が存在しても、採用済み設定ではありません。

正常上書きでは両方成功、隠れる不正2条件だけ方針差が出ます。隠れない不正、boolを整数へ渡した勝者、未知fieldは両方拒否。勝者だけの採用は下位値を修復せず、未検査のまま残します。

## 保存画面の利用

このdirectoryで空いているloopback portを使う例です。保存結果の表示は模型の再実行ではありません。

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

`http://127.0.0.1:8765/` を開き、条件button、方針button、予想button、保存結果を順に操作します。表と図は保存JSONを読むだけです。直接file URLや実application設定適用は確認範囲に含めません。

初回計算と実GUIを完了し、12結果/87時点を手表と保存DOMへ照合しました。現在の受入はstatusを参照してください。[計算記録](MEASUREMENTS.md)と[画面確認](GUI_VERIFICATION.md)を分け、未実行を成功と呼びません。

## 実装と再現

[固定入力](inputs/cases.json)と[手期待](expected.json)は模型実装前に固定しました。[config_model.py](config_model.py)は期待表を読みません。[run.py](run.py)が12結果を1batchへ保存し、[verify.py](verify.py)は模型をimportせず保存JSONだけを検査します。

再現時は現資源と単独枠を確認し、新規出力を使います。今回の実行とは別の手順例です。既存結果の表示に再実行は不要です。

```sh
python3 -B - <<'PYRUN'
import subprocess, sys
subprocess.run(["nice", "-n", "10", sys.executable, "-B", "run.py", "--output", "observations/reproduction-01.json"], timeout=5, check=True)
PYRUN
python3 -B verify.py observations/reproduction-01.json
```

すべて合成JSONで、os.environを読み書きしません。envの厳密parseはJSON文字列自体の構文解析とは別です。元教材はerrorを蓄積しますが、この教材は最初の拒否で停止します。[COVERAGE](COVERAGE.md)のとおり全schema・reload・provider・秘密管理・可用性を保証しません。
