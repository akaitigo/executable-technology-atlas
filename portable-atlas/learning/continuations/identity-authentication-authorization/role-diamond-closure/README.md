# Atlas：同じroleへ戻ったらcycle？

同じviewerへ2経路で到達する菱形は、cycleでしょうか。現在の再帰経路と訪問済み集合を分け、直接権限と継承権限の重なりを消さずに読みます。

[前提](PREREQUISITES.md) → [予想と保存結果](index.html) → [手計算](HAND_TRACE.md) → [原典と実装](reference.html) → [Skillの6問](SKILL.md)へ進みます。現在の実施状態は[status](status.json)が入口です。

最初にlead→writer→viewerとlead→auditor→viewerを辿り、2度目のviewerがactiveに残っているか予想します。次にviewer→leadを加え、開始roleへの戻りと比較します。visitedだけをcycle判定に使う故障は、正しい菱形を拒否します。

この模型は認証やresource取得を行いません。認証済みとscope完全一致は旧教材で学ぶ前提です。成功はrole/permission集合を計算できた意味であり、実アプリのallowや認証成功ではありません。

## 保存結果を開く

Python標準HTTPの例です。この教材directoryで空いているportを使います。

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

`http://127.0.0.1:8765/`を開き、見えている条件button、予想button、「保存結果を開く」を順に押します。前/次の時点は保存traceだけを移動し、新しいpolicy評価を実行しません。直接file URLは確認対象外です。

初回の模型計算は保存済みです。5結果41eventを手期待へ照合し、画面は保存値を読みます。初回HTTP画面で全41時点と境界操作を確認しました。初回画像10枚に、戻り線の配置だけを直した2幅の追補画像を結んでいます。[計算の記録](MEASUREMENTS.md)、[画面の範囲](GUI_VERIFICATION.md)を分けます。

## 実装と再現

[固定入力](inputs/cases.json)と[手期待](expected.json)を先に保存しました。[role_model.py](role_model.py)は期待表を読まず、[run.py](run.py)が5比較を1batchで出力します。保存値だけを読む[verify.py](verify.py)はproducerをimportしません。

再現時は現在の負荷と他の重い処理を確認し単独枠を確保、新しい出力名を使います。今回の実行とは別の手順例です。targetは1子、nice10、wall5秒、自動retryなしで、既存結果は上書きしません。

```sh
python3 -B - <<'PYRUN'
import subprocess, sys
subprocess.run(["nice", "-n", "10", sys.executable, "-B", "run.py", "--output", "observations/reproduction-01.json"], timeout=5, check=True)
PYRUN
python3 -B verify.py observations/reproduction-01.json
```

権限の種類が同じでも出所roleは複数あります。未知roleや評価不能を「権限が空の成功」と扱わず、評価拒否の形式を呼出側へ渡す設計を判断します。[限界](COVERAGE.md)のとおり全RBAC・OAuth・実強制・全graph正当性は今回の保証ではありません。
