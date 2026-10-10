---
name: atlas-api-problem-status-boundary
description: Atlasの固定応答を使い、伝送状態の入力とProblem Detailsのadvisory status、利用側の保留方針を分けて説明する。
---

# Atlas：エラー形式とstatusの判断

最初に[旧APIの契約](related.html?topic=api-readme)と[旧consumer](related.html?topic=api-client)で、通信受信・業務エラー・契約拒否を区別する。次に[今回の画面](index.html)、[契約](CONTRACT.md)、[保存結果](observations/run-01/results.json)、[実行時のconsumer](observations/run-01/inputs/consumer.py)、[原典](SOURCES.md)、[限界](COVERAGE.md)を対応させる。対象計算1回とGUI確認の段階は[確認状態](qa/reader-acceptance.json)で区別する。

1. 「本文status=200なら成功か」には`problem-mismatch`を使い、transportStatus=422、判断の候補値chosenStatus（hold時は未採用）、hold/successを別々に示す。保留は今回のconsumer方針で、故障のsuccessは業務成功の観測ではない。矛盾の原因は断定しない。
2. 「statusが無い/文字列なら応答全体を拒否するか」には`problem-omitted`と`problem-status-string`を使う。型違いmemberを無視したbodyStatus=nullと、伝送状態422を残す。全schema境界を測定したとはしない。
3. 「日本語titleやextensionで別のエラーになるか」には`problem-matching`と`problem-title-extension`を使う。同じtype URIを主識別子にし、titleの翻訳と未知extensionを分離する。URIを自動取得しない。独自形式は`custom-error`と旧契約へ戻す。

この3問は独立担当が保存した12応答と前提・原典・限界への導線を辿って確認した。GUIでも本Skillへの実リンク操作と本文表示を確認した。資料を辿る有限利用確認であり、一般Agent評価ではない。実HTTP、認証、proxy原因調査、再送安全性の要求は[範囲](COVERAGE.md)へ案内し、勝手に外部APIを起動しない。旧教材や共有計画を書換えない。
