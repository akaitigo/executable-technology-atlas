# Atlas：時計順と因果の経路は同じか

この教材は、P/Qの6イベントの全15組を、入力の辺から得た因果関係と比較する。時計計数やversion vectorの新作ではなく、既存の説明を有限の手表と照合するための教材である。

まず [前提](PREREQUISITES.md) → [予想と比較の画面](index.html) → [原典・実装](reference.html) → [限定Skill](SKILL.md) と進む。元教材の場所は [sources.json](sources.json) で示し、単体HTTP配信の外へ飛ぶリンクを成功した導線と扱わない。

**現在の実行・受入は [status.json](status.json) を参照する。** 未接続の測定結果を手期待で補わない。対象を起動する前でも、契約・固定入力・手表・コード・原典は読める。

初回の小計算と検証結果は [MEASUREMENTS.md](MEASUREMENTS.md)、既存ページでの実操作・10画像の確認範囲は [GUI_VERIFICATION.md](GUI_VERIFICATION.md) に保存した。現在の独立受入は状態記録を参照する。

## 何を比べるか

P:a→b→c、Q:d→e→f、メッセージa→e/f→cが固定入力である。予想は因果11組・並行4組。同じ辺で表示順だけ変えても関係は同じ。時計の大小を因果と逆推論すると2組、R1の画面順を辺にすると4組を誤って加える。[15組の手表](HAND_TRACE.md)は実装前の期待であり、実測ではない。

R1とR2は入力の辺を守る表示順で、固定時計昇順のLamport全順序ではない。R1のb2→d1、R2のf3→b2という表示上の減少も合法である。どちらも同じ時計ラベルを使う。

## 利用・再現

Python標準ライブラリと既存ブラウザーだけを使う。画面は `index.html` をHTTP配信して開く。例えばこのディレクトリで `python3 -m http.server 0 --bind 127.0.0.1` とすると表示されたportで利用できる。これは利用者向けの再現手順で、作者が今回サーバーを起動した記録ではない。`file://`の直接利用は検証対象外。

Markdown/Pythonのリンクは配信MIMEにより表示またはダウンロードとなる。資料の内容確認と実画面表示は別に記録する。外部原典のクリック先をローカル遮断noticeで置換した検査は、外部本文を読んだ検査ではない。

計算の保存結果がある場合は `python3 -B verify.py observations/<attempt>/run.json --mutations` で保存値を照合できる。producerは実行しない。現在の採用先は状態記録から確認し、未実行時に存在しないファイルへの検査成功を主張しない。

新しい計算を行うときは [RUN_CONDITIONS.md](RUN_CONDITIONS.md) の資源・優先度・有限回収を先に確認する。rootの現在の所有参照と今回だけのdecisionを固定し、専有枠/GUI idle/他対象0が明示された後に限り、次の手順を使う。

```sh
python3 -B resources.py --root-slot '今回の枠とidleの根拠' --decision /absolute/path/current-decision.json --execute-slot --gui-idle --other-targets-zero
python3 -B run.py --execute --resource-record records/resources-<timestamp>.json
python3 -B verify.py observations/<attempt>/run.json --mutations
```

不成立はtarget0、実行失敗は途中結果を残し、自動retryしない。成功を検証した後だけ `python3 -B build_bundle.py --run /absolute/path/to/observations/<attempt>/run.json` で画面用の完全bytesを結ぶ。旧実行ログと失敗は上書きしない。通常の読取に再計算は不要である。

## 判断と限界

因果の経路を示すには、プロセス内順序と同一メッセージの送受信という根拠が要る。画面で先、時計が小さい、同じ時計というだけでは根拠を追加しない。この模型の「並行」は両方向に経路がないことであり、CPU同時実行や物理時刻の一致ではない。

実ログの欠損、未観測通信、任意グラフ、実分散transport、一般のcausal consistency/linearizabilityは保証しない。[COVERAGE](COVERAGE.md)へ残る問いを記載した。元ownerは未確認で、共有repoへ統合しない。実画面・独立受入・一般Agent評価・教材数判断は別の状態として扱う。
