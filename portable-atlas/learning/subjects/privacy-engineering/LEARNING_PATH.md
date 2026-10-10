# Privacy engineeringを学ぶ道筋

この文書は[識別子除去と群計算の既存教材](README.md)から、QIの選択、属性情報、複数release、確率的保証へ進むための補足です。有限教材の補足であり、分野全体の学習完了や現実のprivacy保証を示すものではありません。以下の次実験はすべて未実行です。

## 1. 前提と仕組み

表の列、projection、grouping、集合、件数、確率分布を理解します。元データ、変換結果、公開用release、内部のlineage原票を分けます。既存の12件は全て架空で、実在人物・地域との対応はありません。

学ぶ順序は **用途と必要データ → 直接識別子・QI → 一般化と群サイズ → 属性情報・utility → auxiliary情報と複数release → DP等の機構 → retention・access・運用** です。

- 直接識別子を消しても、複数列の組合せで1件だけの群が残り得ます。
- kは指定QIで作った群のサイズ条件です。実再識別確率、属性開示防止、完全匿名、differential privacyとは違います。
- 一般化は変換方法、kは検査閾値です。閾値変更だけでtableが変わるとは限りません。
- 集計tableのrow数と、集計前microdataの群サイズを分けます。countを出すだけでprivacy保証が成立するとはしません。

## 2. 予想から既存実測へ

[UI](index.html)、[実装](runner.py)、[独立手集計](hand-groups.json)、[原票](evidence/observation.json)、[環境・digest](evidence/verification.json)、[QA](QA.md)を読みます。この文書作成では変換・checker・UIを実行していません。

| 形式 | 保存済み出力 | 指定QIの元レコード群 |
|---|---|---|
| 識別子除去 | age/zone/category、12row | 12群、最小1 |
| 一般化 | age_band/zone_group/category、12row | 3群、最小4 |
| 一般化後count | age_band/zone_group/count、3row | 集計前は3群、最小4 |

正常な変換で、直接識別子はrelease列から除かれます。しかし「名前を消せば大きな群」という予想は最小1の結果で外れます。一般化の群サイズはk=2/4を満たし、k=5は未達です。閾値を変えても変換は同じで、未達群を隠したり削除したりしません。

一般化でもcategoryは残り、架空A群は全て同じcategoryです。群サイズ4から属性情報の保証を導けません。count形式ではcategoryと個別rowがなくなり、使える分析も変わります。空tableのminimumとsize条件はnull / undefined-emptyで、合格ではありません。不正型・欠損・null・重複IDは拒否する検査が記録されています。

9条件と空境界は架空入力の計算です。QI選定、外部linkage、現実の再識別、l-diversity/t-closeness、DP noise/budget、法的適合の実証はありません。内部原票のsynthetic_id保持はrelease列への混入と違いますが、このbundleを実データの公開方法へ流用できるという意味でもありません。

## 3. 実務で何を判断するか

何の用途でどの列・粒度・期間が必要かを先に決め、releaseの受取者、アクセス範囲、外部情報、繰り返す更新も考えます。群サイズだけでなく、残る属性情報、utility、複数releaseからの推論を別々に評価します。

DPを扱う場合は隣接関係、保護する単位、mechanism、epsilon/delta、compositionを明示します。データの名前削除やkの変更をDPと呼びません。暗号化やアクセス制御も別の役割を持ち、公開後に得られる推論まで単独で消すものではありません。正式なrisk評価や適合判断はこの架空教材の範囲外です。

## 4. 一次資料への道筋

| 原典とlocator | 読む目的 |
|---|---|
| [NIST SP 800-188, September 2023](https://doi.org/10.6028/NIST.SP.800-188)、§2.2 / §4.3 | 識別子、QI、変換と限界の既存binding |
| 同文書§4.3.8 / §4.3.11 | aggregationとcompositionで残る推論 |
| [Dwork & Roth, The Algorithmic Foundations of Differential Privacy](https://www.cis.upenn.edu/~aaroth/Papers/privacybook.pdf)、Definition 2.4 / §3.2 Randomized response / §3.5 Composition | 出力分布の比較、randomized response、繰返しreleaseの予算 |

既存locatorは[sources.json](sources.json)にあります。NIST資料の概念接続と、このfixtureの具体的な群計算を分けます。DPの定義はrelease機構の性質で、単一の出力tableに付ける万能な安全ラベルではありません。

## 5. 未教材の問いと次実験

| 未教材 | 問い | 次の入口 |
|---|---|---|
| QI選定・属性開示 | QIを増やすと群が変わり、同質categoryは何を示すか | 実験1 |
| utility・一般化の選択 | 保ちたい集計と失う精度をどう測るか | 実験2 |
| auxiliary情報・複数release | 個別releaseが粗くても組合せで何が分かるか | 実験3 |
| DP・epsilon・composition | 近い入力の出力分布と繰返しの保証は何か | 実験4 |
| suppression・l-diversity・t-closeness | 群サイズ以外の制約をどう定めるか | 別の定義と検査が必要 |
| purpose/consent・retention/deletion・access・DPIA | データの利用と生命周期をどう管理するか | 正式な要件・risk評価は未実施 |
| PETs・MPC・federated analysis・実synthetic生成・監視 | 何を誰から守り、何が残るか | この表変換では未評価 |

## 6. 次の実験案（4本、すべて未実行）

1. **QI追加と属性の同質性を比較する。** 架空fixtureのコピーでQIをage_band/zone_groupだけの場合とcategoryも加える場合に分け、各群のID集合とサイズを手書き表へ照合します。予想は列追加で群が細分化し得ることです。categoryをQIにしない条件では、群内categoryの異なる値の数も保存し、全同値群と混在群を比較します。原典はSP 800-188 §2.2 / §4.3です。distinct数の小さな集計を完全なl-diversityや現実の属性開示risk保証と呼びません。

2. **用途を固定してutilityを測る。** 架空データで全体件数、年代別件数、category別件数、平均年齢という4問いを先に定め、drop/generalize/countの出力からどれを計算できるかを表にします。一般化の年齢を帯の中点で近似する条件は独自規則と明記し、元入力の手集計との差と計算不能を別に保存します。予想は集計の用途によって残る情報が異なることです。原典はSP 800-188 §4.3の変換です。utility改善をprivacyの保証へ変換しません。

3. **2つの架空releaseの差分を比較する。** category別countの2時点を用意し、2時点の間に合成1recordだけが追加されたという情報を与えます。予想は個別rowを出さなくても、count差分から追加recordのcategoryが分かる条件があることです。全categoryの差分と、事前に手書きした推論可能/不能表を照合します。変更が複数ある対照例も作り、推論に使った仮定を明記します。原典はSP 800-188 §4.3.8 / §4.3.11です。外部データ取得・実人物のlinkage・実再識別は行わない案です。

4. **randomized responseの分布を有限列挙する。** 架空の1bit入力0/1で、公平coinにより半分は真実、半分は別coinで答える機構を定義します。乱数sampleではなく全coin経路と正確な確率を列挙し、同じ答えの確率3/4、反対1/4という手書き表へ照合します。予想は入力間の各出力確率比が最大3で、独立に2回答をreleaseすると同じ方向の出力対の最大比が9になることです。隣接関係を「その1bitが異なる」と明示し、Definition 2.4の分布比較と§3.2・compositionに接続します。これは局所的な有限機構の理解案で、既存12件releaseのDP化、一般DBの隣接関係、privacy accountant、実サービス保証は未実装です。

## 7. 資料の取得・検証状況

2026-10-05にNIST SP 800-188のPDF本文と、Roth著者の大学サイトのDP原典PDF本文を取得して参照箇所を確認しました。今回取得不能だったURLはありません。第三者本文・図・実人物データは教材へ保存していません。

追加したのはこの文書だけです。表変換、DP機構、checker、外部linkage、server、UI、global gateは実行せず、既存原票・QA・digestを更新していません。次実験の予想は新たな実測証拠ではありません。
