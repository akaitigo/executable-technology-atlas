# 名前を消した。それで同じ群になった？

架空12件をPython標準ライブラリで実処理し、直接識別子の除去、指定したquasi-identifier（QI）の一般化、群ごとのcount集計を比較する1教材。実在人物への対応や外部データとのlinkage、現実の再識別は行わない。zoneとcategoryは教材内の架空記号である。

## 予想 → 操作 → 比較

1. 名前とsynthetic_idを消しても、age + zoneの組合せが1件しかないrowは残る？
2. ageを10歳帯、zoneを先頭記号まで粗くすると、群サイズは何件になる？
3. kを4から5へ変えるだけで、出力tableは変わる？
4. 群countだけの出力にすると、何の情報が使えなくなる？

[画面](index.html)で3つの出力形式とk=2/4/5を選ぶ。画面は保存済みPython原票を表示する説明モデルで、新たなreleaseや外部送信はしない。群サイズ図、実際の出力列・row、情報の粗さを見比べる。

## 追試と明示更新

Python 3だけ。依存導入、Docker、外部APIは不要。

```sh
python3 -B verify.py
python3 -B observe.py --check
python3 -B runner.py --mode generalize --k 4
```

通常checkerはread-onlyでbytecodeも書かない。保存原票を明示的に更新するときだけ `python3 -B observe.py --write` を使う。全memberのstaging検証後にbundleをpublishする。source/input変更はcheckでstaleとして拒否する。

一時画面確認はこのmoduleをworking directoryとして次を実行する。

```sh
python3 -u -m http.server 0 --bind 127.0.0.1
```

表示された動的portで `http://127.0.0.1:PORT/index.html` を開く。他担当のserverを停止しない。終了はこのserverをCtrl-C。実IAB QAでtitle/module fieldを確認する。`file:`直接openは未検証。

## 原典 → 実装 → 手集計

[NIST SP 800-188](https://doi.org/10.6028/NIST.SP.800-188) §2.2と§4.3は、直接識別子とQI、群サイズによる考え方、一般化の制約を読む入口。本教材のage/zoneは便宜的にQIと指定したもので、実データの専門的QI選定やrisk assessmentではない。原典の本文は保存しない。[sources.json](sources.json)にURL・section/page locator・対応範囲を保持する。

[fixture.json](fixture.json)はoriginal架空データ。[hand-groups.json](hand-groups.json)にはfixtureのsynthetic_idから独立に手で列挙した全群と期待sizeを固定し、runner出力から期待値を生成しない。[runner.py](runner.py)はprojection・generalization・aggregationを実行し、[verify.py](verify.py)で照合する。

## 答えと境界

| 出力形式 | 出力列 | 出力row数 | 指定QIの元レコード群 | 最小群サイズ |
| --- | --- | --- | --- | --- |
| 識別子除去だけ | age / zone / category | 12 | 12群 | 1 |
| 一般化 | age_band / zone_group / category | 12 | 3群 | 4 |
| 一般化後の群count | age_band / zone_group / count | 3 | 3群 | 4 |

名前等を消しても、age/zoneの組合せでは全12件がsingletonのまま。一般化では4件ずつの3群となり、この指定QIのsize条件はk=2/4なら満たすがk=5では未達。kは検査閾値であり、変更しても変換処理は変わらない。未達群を自動隠蔽・削除・安全化しない。

これは指定QI上のk-anonymity風の群計算だけで、全privacy保証や実際の再識別確率ではない。集計時のsize=4は集計前の元microdataの群サイズであり、3 rowのcount tableそのものに「k=4のprivacy保証」を与える表示ではない。集計ではcategoryと個別rowを出力しないため、個別値を使う分析はできなくなる。

一般化でもcategoryは保持される。架空A群のcategoryは同一値だが、属性開示の保証・l-diversity・t-closenessは検査していない。外部auxiliary情報、QIの追加、複数releaseの相互作用、順序やside informationは未検証。元入力・audit群のsynthetic_idは教材のlineage原票として別に保持するが、release列へ混入させない。全raw bundleを実データの公開手段として使わない。

空tableは群minimumもsize条件も `null / undefined-empty` とし、空だから合格とは扱わない。null・型不正・欠損・不明field・重複IDは明示拒否し、null同士を大きな安全群に数えない。

## 保存証拠と未教材Coverage

実行時刻・Python環境・input/raw/source/artifact SHA-256、checker raw結果は [verification.json](evidence/verification.json)。[observation.json](evidence/observation.json)は9条件と空境界の実出力。[QA.md](QA.md)は実IABとSkill smokeの確認範囲。source digestはlocal実装とlocator fileを束縛し、remote authority本文のlockとは主張しない。

loss/utilityの定量評価、外部auxiliaryや現実再識別、属性開示/l-diversity/t-closeness、suppression/最適一般化、differential privacyのnoise・epsilon・composition、正式なrisk評価・法的適合は未教材。k値はdifferential privacyではない。

Subject全体のdata minimization、purpose/consent、retention/deletion、access control、privacy threat modeling、DPIA、governance、PETs/暗号化・MPC・federated analysis、実synthetic生成、auditing/monitoring、deployment/interoperability、incident対応・運用も未教材。Subject完成や現実のprivacyを保証しない。旧Goal/full Gateの未完stateは変更しない。

[限定Skill](skills/atlas-privacy-engineering/SKILL.md)はこのrunner/checker/UIにだけrouteする。
