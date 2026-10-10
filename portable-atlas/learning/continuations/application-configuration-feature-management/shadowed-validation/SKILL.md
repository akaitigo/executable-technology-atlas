---
name: atlas-config-shadowed-validation
description: 保存した2つの検証方針を読み、隠れた不正値・型・候補と公開設定を分けて判断する。
---

# 検証した範囲を答えに添える

[status](status.json) → [前提](PREREQUISITES.md) → [README](README.md) → [保存結果](observations/attempt-01.json) → [原典と実装](reference.html)の順に読む。未実行で保存結果が無ければ[手表](HAND_TRACE.md)・契約・コードまでに限定する。GUI保留時は新browser/serverを起動せず、本文と保存JSONを使う。保存値を読むためのtarget再実行は不要。

次の6問を、case/policy/event→attempts/candidate→config/provenance→限界へ辿る。

1. shadowed-integerでなぜ2方針が分かれるか。winning-onlyがenvのoopsをparseしていない記録を示す。
2. unshadowed-integerではretries=3の候補があってもなぜconfig=nullか。候補と公開を分ける。
3. invalid-winning-boolのtrueは数値1として受理されるか。型とrangeの判定順を確認する。
4. shadowed-booleanのnative falseと文字列TRUEは同じか。未検査の下位値と成功値falseを区別する。
5. unknown-fieldは両方でいつ拒否され、どこにrawが出ないか。入力fixtureの保存と結果の非転載を分ける。
6. 上位指定を後で外す運用では何が起こり得るか。全層/勝者のみを要件へ結び、atomic reloadやOpenFeature保証と混ぜない。

これは6入力の保存資料を使う限定読取で、一般Agent能力や全applicationの安全性評価ではない。新実行は現資源/単独枠/優先度/期限/所有回収を確認して新保存先へ。任意schemaや実環境/remote providerは別途検証する。
