---
name: atlas-reflow-focus
description: この有限reflow/focus教材の4条件をMac IABで再採取し、保存原票を監査する。全WCAG適合監査やBrowser zoom測定には使わない。
---

教材rootはこのファイルから `../..`。[README](../../README.md)、[期待表](../../EXPECTATIONS.md)、[採取手順](../../REPRODUCE.md)を読む。通常監査と新しいBrowser観測を分ける。既存accepted単位・元Skill・QE/globalは変更しない。

通常監査はrootで `python3 -B checker.py`、`python3 -B test_negative.py`、`python3 -B route.py reflow`。すべてread-only。bindingの不一致を消してpassにせず、どのsource/観測が変わったか調べる。記録やbinding更新はその教材の変更・新採取が依頼された場合だけ明示実行する。

新採取は `python3 -B server.py` の専用dynamic loopbackと専用IAB tabを使う。起動前に適用AGENTSとadmissionを確認。予想を入力し、fixtureのfixed/fluid×1000/320 CSS px（高さ800）の4条件を操作する。公開されたviewport capability docsを確認して一時setし、要求値でなくDOM client/inner寸法を採取する。条件選択だけではviewportは変わらない。公開APIに実zoom手段がなければUNMEASUREDとし、OS/アプリ設定や新権限へ進めない。

Tab開始点click→Tab5回。person/email/category/agree/sendの各activeElement、trusted Tab/focus列、scroll寸法、computed outline、全control rect、center hit、cover overlap、UTCを保存。fresh native AXとnative captureを別採取し、DOMからAXを推測しない。Enterで合成送信0→1を確認。viewport外のhit=nullを遮蔽なしと扱わない。outline0だけで全indicator不在とせず、partial clippingも原票のまま残す。

fixed→fluidは幅・outline・coverの3変更セット。幅単独がfocusや遮蔽を修復した証拠ではない。viewport縮小≠Browser zoom。AXにcontrolがあることと画面で見えることを区別する。contrast/AT/media/touch/forced colors/全WCAGは未教材。

旧attempt/source/captureを保持して新採取を別記録。source SHAを記録した保存観測をUIで再表示し、予想編集、条件reset、503、古い保留結果の無視、source/raw/Skill viewerを確認する。誤予想・失敗・未観測を成功へ上書きしない。checkerと負例、通常CLI前後SHA/mtime不変を確認。自分のviewport overrideをresetし、専用tab/serverだけ終了。開始時に確認した保護listenerを維持する。インストール、公開、commit/pushを含めない。
