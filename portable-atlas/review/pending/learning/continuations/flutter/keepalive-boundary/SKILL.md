---
name: flutter-keepalive-boundary
description: ListViewの画面外でStateを保持する条件を、祖先wrapper・子の要求・cached状態に分けて予想し、固定ソースと実Widget原票で確認する。
---

# 画面外の保持と破棄を確認する

この教材内で使うローカルSkillです。固定2条件×4段階の実Widget観測、別Python実装191確認、保存実測readerのGUI/画像QAが成功しています。固定表は実行前の予測として保持し、実測原票とは区別します。別担当の最終受入は[現在の記録](ui-qa/reader-acceptance.json)を参照します。インストール・公開済みとは扱いません。

1. [README](README.md)の要求を読み、同じStateを画面外でも保持したい場合と、業務データを保存したい場合を分ける。
2. `addAutomaticKeepAlives:true`は両条件で同じと確認し、子の`wantKeepAlive` true/falseが生存にどう影響するか予想する。
3. `python3 serve.py`で[index](index.html)を開く。条件と予想を選び、遠方の保存実測を再生し、先頭へ戻る。layoutとcached、4個の生存Stateと画面内2項目を分けて対照比較する。GUIは保存原票の選択・再生で、Flutterライブ操作ではないと伝える。
4. 固定ソースと実行時snapshotでmixinの`super.build`契約、祖先への通知、Sliverの保持/破棄処理を読む。`wantKeepAlive`が変わる場合の`updateKeepAlive`契約は説明するが、今回の値は一定と伝える。戻り時点で予想と照合する。
5. 予想/条件/resetで古い結果が消えることを確認する。読込失敗を古い成功や推測値で補わない。再実行が必要な場合だけ[再現手順](REPRODUCE.md)の資源条件とrootの実行枠を確認し、専有pathへ1短batchを行う。
6. State ID・回数・disposeと公開`keptAlive`区分を照合する。別Pythonチェッカーは実行を重ねず原票を読む。cachedのText読取は実画面captureと区別する。予測不一致や失敗も保存する。
7. 同じtree内でのState生存、業務データの所有、processを越える復元を分けて判断する。reorder・動的切替・外部保存・性能・FlutterライブGUI/pointer/drag・Flutter描画画像の未対応範囲を残す。readerの実Chromium画像をFlutter描画と混同しない。

この単元の有限な受入が終わったら、成果・証拠・残項目を返します。別単元へ自動的に範囲を増やしません。
