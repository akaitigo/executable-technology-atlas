---
name: atlas-supply-chain-provenance-policy
description: Atlasの固定7条件で、来歴申告と別保持policyの比較を読む。署名検証やreleaseの許可には使わない。
---

# Atlas｜来歴の期待を読むSkill

[読む順](README.md)→[元の学習経路](related.html?topic=path)→[契約](CONTRACT.md)→[画面](index.html)→[原典](SOURCES.md)→[範囲](COVERAGE.md)を辿ります。[手期待](expected.json)と[保存結果](observations/run-01/results.json)を区別し、[確認状態](qa/reader-acceptance.json)の実施範囲を先に確認します。

1. 「checksumが合うならbuilderも正しい？」にはnormalとother-builderを比べる。artifact_digestは両方一致、builder_idだけ不一致になる。内容と別保持の期待を分け、[既存digest/baseline](related.html?topic=digest)へ戻る。
2. 「同梱のpolicyに合えばよい？」にはother-builderとbundle-policy-replacedを比べる。同じclaimsに対して正常版は同じ不一致で、故障版だけ変わる。正常版が受信proposed_policyを参照しない実装境界を確認する。unknown-parameterではparameter_valuesは既知keyだけの一致で、parameter_keysの不一致を消さない。
3. 「一致したから署名済み・安全にreleaseできる？」には全件のnot-run／null／out-of-scopeを示す。claimsの文字列比較は生成者認証でなく、[原典のStep 1とStep 2](SOURCES.md)と[未対応範囲](COVERAGE.md)へ戻る。実署名・鍵・失効・本物のbuild・releaseをこのSkillから開始しない。

独立担当がこの3例を保存計算と前提・原典・範囲へ辿り、資料導線も実画面で確認しました。この有限3例の読取利用を一般Agent評価にしません。署名済み、SLSA level達成、全供給網完成を宣言しません。
