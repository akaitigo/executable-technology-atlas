# Atlas：候補値を戻して次の解へ

4変数2色の小さなCSPで、候補値を削る処理と枝から戻る処理を分けて学びます。「一つ解が見つかる」だけでなく「全解を失わない」ことを、復元を省いた対照と比べます。

読む順は[前提](PREREQUISITES.md)→[画面](index.html)→[手期待](HAND_TRACE.md)→[原典/実装](reference.html)→[Skill](SKILL.md)です。先に各条件の解の数を予想し、削除と復元の時点を操作してから答えを確認してください。

## 比べるもの

- 無辺：全16割当。
- 四角：隣が異なる2解。
- 三角＋孤立D：候補が非空の途中状態から矛盾へ。
- A=0固定の四角：singletonも探索で割り当てる。
- 四角の復元省略：正常終了しても正しい全解から一つ失う設計反例。

最初の4問題をbaseline/FCで比較し、故障版を足した9結果を保存します。固定counterは候補試行・割当済検査・先行検査などを分け、回数を実時間の速さと同一視しません。模型の実行値、手計算、未実施を区別します。現在の実行と受入は[状態](status.json)、画面範囲は[GUI記録](GUI_VERIFICATION.md)です。

## 画面を読む

`index.html`と同じディレクトリをHTTPで配信します。既存Python標準環境だけなら、workspaceで以下を使えます。空きloopback portは利用環境で選んでください。



`http://127.0.0.1:8765/`を開きます。この通常閲覧手順と、rootの既存pageを使うGUI検査は別です。直接file URLの動作は確認対象ではありません。Markdown/コードはサーバーにより本文表示またはdownloadになるため、資料の配信と画面本文を分けて確認します。前提とSkillは専有ディレクトリ内で辿れます。元教材への場所説明は外部HTTP導線の成功を意味しません。

## 保存値と再現

[契約](CONTRACT.md)、[疑似コード](PSEUDOCODE.md)、[入力](inputs/problems.json)、[手期待](expected.json)、[実装](csp.py)を先に固定しました。producerはexpectedを読みません。全stdout/stderr・版・hash・資源・exit・回収を保存し、`verify.py`が保存値を読みます。保存結果を読むための再実行は不要です。

再実行時は[実行条件](RUN_CONDITIONS.md)の新しいscope decisionと単独枠を確認し、以下のCURRENT_DECISION/CURRENT_RESOURCEをその回の記録へ置換します。古いallowedの再使用や自動retryはしません。

```sh
python3 -B resources.py --root-slot '当該枠とGUI idle/他target0の根拠' --decision CURRENT_DECISION --execute-slot --gui-idle --other-targets-zero
python3 -B run.py --execute --resource-record CURRENT_RESOURCE
python3 -B verify.py observations/NEW_ATTEMPT/run.json
```

保存したrunを`build_bundle.py --run ...`で検査してから接続します。新規runの保存先は日時ごとに分かれ、旧結果を上書きしません。

## 判断の限界

今回のFCは割当直後の未割当neighborだけを調べます。三角のB/Cのような未割当同士の伝播を含むAC-3ではありません。全domain非空は解ありの証拠になりません。4変数の全解照合を一般CSP・配置・AI性能・実時間優位へ広げません。[範囲と次の問い](COVERAGE.md)へ。

## 今回の保存記録

[模型の実行](MEASUREMENTS.md)は1子・9結果、[実画面](GUI_VERIFICATION.md)は既存pageの初回1回・10viewportです。計算結果と手期待、独立受入の状態を分けて確認できます。[学習経路用の短い導線](navigation-route.json)も同梱しています。
