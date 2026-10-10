---
name: flutter-globalkey-reparent
description: 別parent間の同frame移動と一度除去した後の再追加を比較し、GlobalKeyによるState保持と保存の違いを確認する。
---

# 移動と削除後の再作成を分ける

この教材内のローカルSkillです。3条件×4時点の実Widget検証、作者の別Python245確認、保存実測readerのGUI/画像QAが成功しました。公開・インストール済みとは扱いません。[現在の受入記録](ui-qa/reader-acceptance.json)で状態を確認し、凍結した事前予測と実測を区別します。

1. [README](README.md)の要求を読み、左のAを右へ移したときのState/回数を3条件で予想する。
2. 同frame条件は1回のsetState、一度除去する条件はframe終端を通ってから再追加すると確認する。GlobalKey自体を毎回作り直さない。
3. `python3 serve.py`でreaderを開き、条件と予想を選んで移動/除去を再生し、「右に置いた後」へ進む。親Slot・直親Element・Tile Element・State ID・回数を残る2条件と比較する。操作は保存実測の再生で、Flutterライブ操作ではないと伝える。
4. 固定公式ソースと実行時snapshotを読み、deactivate/activate/disposeを分ける。移動のためのdeactivateを破棄と即断しない。右へ置いた後の予想と照合する。
5. 予想/条件/resetと読込失敗で古い結果が残らないことを確認する。取得失敗を推測値で補わない。別Pythonの原票照合にはcompilerは不要。不一致を消さず、必要な検証だけ枠・資源条件を確認して行う。
6. Keyが同じでも破棄済みStateを復元するものではないと説明し、保存すべきデータの所有階層を選ぶ。FlutterライブGUI/pointer/drag・Flutter描画画像、重複Key例外、性能、外部復元は未対応として残す。

今回の単元はこの1つです。次の単元や新runtime検証へ無制限に広げず、成果と未確認事項を返します。
