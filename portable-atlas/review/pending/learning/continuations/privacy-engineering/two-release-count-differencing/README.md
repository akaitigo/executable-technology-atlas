# IDのない2つのcountでも、差分は残る

[元Privacy LEARNING_PATH §6実験3](../../../subjects/privacy-engineering/LEARNING_PATH.md)の有限継続。架空category A/B/Cのcountだけを2時点で比較します。**対象の合成1recordが追加され、その後も残っていることは共通知識として与えます。対象が存在すること自体をcountから推定したものではありません。** 実人物・外部dataset・識別子の取得・公表は行いません。

## 先に固定する変化契約

before/after各3整数0..6、target_addedはtrue、背景追加/削除の上限各0..2。削除vectorはbefore以下で、最初のreleaseの背景recordだけから削除。対象や新背景recordの削除は許可しません。背景追加vectorも非負、sum≤上限。上限は『まで』なので0変更を含む。beforeに対象はまだ含まれない、afterには対象が1件残ります。

`after = before + unit(target category) + background_add - baseline_delete` を満たす全count-vector witnessを列挙。各上限2ならadd10vector/delete最大10vector×target3=最大300。countは非負を保ち、削除容量も守る。背景delete+addはcategory変更等のcount変化を表せますが、同一背景recordの対応づけはしません。追加/削除の無限候補や任意モデルへ一般化しません。

候補category1個=known（この前提下のみ）、2個以上=ambiguous、0個=inconsistent（前提/観測の不整合）。候補0を安全・対象不存在と読まない。複数witnessでもcategoryが1個ならknown。witness数は個人数/確率/現実再識別率ではありません。

| 実装前手表 | before→after | 背景add/delete上限 | 候補 | witness数 |
|---|---|---|---|---|
| sole-A | [1,1,1]→[2,1,1] | 0/0 | A | 1 |
| same-delta-background | 同じ2release | 1/1 | A,B,C | 6 |
| empty-baseline | [0,0,0]→[1,0,0] | 1/1 | A（baseline削除容量0） | 1 |
| two-added | [1,1,1]→[2,2,1] | 1/0 | A,B | 2 |
| unchanged-with-deletion | [1,1,1]→同じ | 0/1 | A,B,C | 3 |
| inconsistent | [1,1,1]→同じ | 0/0 | なし | 0 |

同じ差分[1,0,0]で、背景なしなら対象Aが一意。背景add1/delete1なら対象B＋背景A追加＋baseline B削除も整合。対象Bは残り、削除されたのは別のbaseline背景Bです。Cも同様。故障版は背景上限/削除容量を無視して差分+1のAを断定し、候補集合を隠します。countには直接IDがなくても、強い共通知識の下でcategory推論が残る反例です。曖昧化した一例がprivacy保証ではありません。

[手表](hand-oracle.json)/[producer前SHA](qa/oracle-before-producer.json)を先に固定。producerは全add×delete×target候補を走査。[checker](checker.py)はdeleteを別の三重loopで列挙し、等式からaddを解く独立oracle。全witness集合の完全一致/重複なし/category集合/0候補を検算。12mutantで背景無視/候補欠落/重複/対象削除/0をknown/曖昧をsafe/差分逆/上限無視/対象存在推定/確率/実linkage/DP偽称を拒否。

## 予想 → 前提操作 → 正常/誤推論 → 原典/原票 → 答え

[画面](index.html)で2時点棒/差分、candidate集合とwitness数、全witness表を表示。『背景add/deleteを1まで許す』はcountを変えず1操作で前提を変え実childへ送り、一意A→A/B/Cへ変わる。名前削除だけで推論を防ぐ保証ではありません。JSON/例/予想/明示resetで旧図/候補/原票/答えを空にしdetailsを閉じる。遅延結果を変更後に復活させず、通信/child失敗に正常答えを作りません。

```sh
python3 -B checker.py
python3 -B runner.py
python3 -B qa/check-ui.py
python3 -B server.py
# 明示採取のみ新UTC固定原票
python3 -B runner.py --record
```

通常checker/runner/QAとmemory-only server起動/GET/POST/exportで全unit SHA/mtime不変。RAM512件、停止で失効。明示QA採取のみ専有dirへ保存、新serverは新原票。固定allowlist escaped text viewerでsource/Skill/手表/元LEARNING_PATHを表示し、任意path不可。既存RR/旧教材/QE/global/manifestと保護53478/60285/50835は変更なし。既存Python標準libだけ、install/課金/新権限/公開/commit/push/fullGateなし。

## 原典との接続と未実証

[NIST SP800-188 September 2023](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-188.pdf) §4.3.8（印刷pp57-58）は複数集計releaseで残る推論、§4.3.11（pp59-60）はrelease結果を組み合わせる際の課題へ結びます。NISTの例の値や人物属性は流用せず、A/B/C値とbackground契約は教材独自。単純count差分の有限反例で、実再識別率・法適合・DP guarantee/composition accountantではありません。[sources](sources.json)/[COVERAGE](COVERAGE.md)/[Skill](skills/atlas-two-release-count-differencing/SKILL.md)/[QA](qa/README.md)。中央受入待ち、分野完成や旧RRのDP保証拡張は宣言しません。
