---
name: atlas-static-type-boundary
description: Atlasの固定5閉項で、型判断と通常評価・診断比較を区別して保存証拠へ案内する。
---

# Atlas：静的型判断を読む限定Skill

最初に [status.json](status.json) を読む。完了した測定がなければ [契約](CONTRACT.md)・[手期待](expected.json)・[手読解](HAND_TRACE.md)・[原典](SOURCES.md)・コードの説明で止め、模型を実測と呼ばない。保存実測があれば状態記録が指すrunと [画面](index.html) で該当条件を照合する。GUI未確認や起動保留は別状態として尊重し、Skillを読むだけでbrowser/server/producerを開始しない。

有限6問を、予想→判断または比較→根拠→限界の順で案内する。

1. Γは実行時の値辞書か。関数の引数型を加えたcontextを規則木で追い、名前→型と説明する。
2. 関数を引数に渡す条件の型はどう決まるか。domainと引数型、body型、全体Intを手表と保存結果へ照合する。
3. 型拒否した整数callは通常経路で何回評価するか。strictの0回と、診断の1回/stuckを別列で読む。
4. 関数に整数を足す拒否はどこか。$.leftのArrowと必要なInt、未検査のrightを確認する。
5. 未呼出関数は値なのに拒否されるか。本体の型拒否とFn value/0歩を対照にし、型検査を本体実行と呼ばない。
6. 有限5条件から一般型安全性を言えるか。[COVERAGE](COVERAGE.md) へ戻りprogress/preservation・注釈なし推論・未観測枝は別課題とする。

[前提](PREREQUISITES.md) から束縛/置換/小ステップへ戻る。workspace外の旧pathは出所であり、単体HTTPから利用できた証拠としない。原典の可変ページ、固定比較source、型注釈消去規則の違いは [SOURCES](SOURCES.md) / [sources.json](sources.json) で確認する。このSkillの有限読取確認と一般Agent評価は別である。

再現は [RUN_CONDITIONS](RUN_CONDITIONS.md) の資源・専有枠・新fresh・実nice・期限・所有子回収を満たすときに別保存先へ。閲覧だけなら再計算不要、旧結果は上書きしない。
