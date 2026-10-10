# Application configuration / feature management — どの設定で誰に有効か

架空のクラウドapplication設定とfeature flagを扱う有限モデル。Python標準ライブラリだけで18ケースを実行し、優先順位・型・拒否・固定actorのrolloutを独立oracleで照合する。実環境設定やSLAを保証する教材ではなく、科目全体の完成でもない。

前提はJSONのstring/bool/int、mapping、default、actor key、内容hash。[index.html](index.html) でdecision・有効actor数・選択fieldの勝者layerを予測し、ケースとfieldを操作して比較する。「入力layer → typed parse → precedence → validation → actor判定 → raw/原典 → 答え」の道筋を通す。UIは保存済みの実行readerでありブラウザ操作は設定適用やevaluator再実行をしない。

前単位data-governance-quality-lineageはdataset品質contractと由来・cache失効を扱った。本教材はapplicationの設定値とfeatureの評価を扱う。provenanceはdataset列ではなく、最終fieldがdefault/env-input/task-jsonのどこから来たかを示す。

defaultはtimeout_ms=1000、retries=2、flag_enabled=true、rollout_percent=50。env-inputはJSON内の架空string mappingでありos.environを読み書きしない。対応はAPP_TIMEOUT_MS/APP_RETRIES/APP_FLAG_ENABLED/APP_ROLLOUT_PERCENT。task-jsonはnative JSON値。優先順位はdefault → env-input → task-json。上書き履歴にはsource field、raw、typed、priorを、最終provenanceには勝者layerを残す。

strict booleanはenvの厳密な小文字true/falseだけを受理し、taskはnative boolのみ。integer stringは正規の十進文字列のみ、task integerはboolを除く。範囲はtimeout_ms 1..5000、retries 0..5、rollout_percent 0..100。未知fieldは値をevaluator traceに転載せず拒否する。fixtureのapi_key/APP_SECRETはEXAMPLE_NOT_A_SECRETという架空文字列。secret managerや実credentialを扱わない。

通常は50%でalpha/gammaが有効。envでfalseを指定すると全actorがmaster-disabled。task-over-envではtimeout 2000→3000、flag false→trueとなり75%でalpha/gamma/deltaが有効。文字列falseのstrict parseではfalseだが、意図的truthiness-bugではbool('false')=trueとなり100% rolloutで4人とも有効になる。Pythonで非空文字列がtruthyなことを実測する比較である。

rolloutは固定salt demo-v1、NUL区切り、actorのUTF-8 bytesをSHA256し、先頭8 hexの整数 %10000をbucketとする。bucket < rollout_percent*100かつmaster flagがtrueなら有効。alpha=2710、beta=7590、gamma=3562、delta=5260。0%は全off、100%は全on。stable-repeatでは同一alphaを再評価して同一hash/bucket/判定を確認する。この独自アルゴリズムはprovider互換仕様や統計的実験の保証ではない。4 actorの実比率がpercentに一致する保証もない。

境界は設定範囲上下限、0/100% rollout。拒否は大文字TRUE、oops integer、timeout=0、percent=101、bool-as-int、task文字列false、未知secret field/未知env field。拒否時はconfig=null、actors=[]として不完全な設定を利用しない。各layerを順に検証するため、後のlayerで上書き予定の不正値も拒否する方針。shadowed invalidのfixtureは今回未実行で次の実験に残す。

実務では「同じ文字列を渡した」ことより型と勝者layerを確認し、boolと数値を区別し、actor identity/saltを固定してrollout安定性を判断する。master flag falseとbucket外をreasonで区別する。timeout値はここでは設定だけで、実リクエストtimeoutやretriesを実行した証拠ではない。入力誤りを拒否するかfallbackするかはapplication要件による。

```sh
python3 runner.py                          # defaultはread-only確認
python3 checker.py
python3 test_negative.py                   # 一時コピー5種の改竄 + read-only確認
python3 runner.py --record                 # 明示した原票更新だけ
python3 preview.py                         # 一時dynamic loopback、終了時Ctrl-C
python3 skills/atlas-application-configuration-feature-management/route.py config-flags
```

[current.json](current.json) からUTC時刻/OS/Python、input、commandのstdin/stdout/stderr/exit、raw trace/result、独立oracle、source/artifact SHA256へ到達する。[checker.py](checker.py) はevaluator/runnerをimportせず、固定raw→typed表、拒否理由、provenance、固定actor hash/bucket/有効集合を検査する。SHA256 digest計算そのものはstdlibを利用し、rollout期待値は固定表。[qa.json](qa.json)・[verification.json](verification.json)・[ui-observations.json](ui-observations.json) に実画面QAと検査を保存する。

未カバーはschema evolution、dynamic reload、last known good、remote provider/cache/outage fallback、targeting/context/variants、salt/ID変更、flag owner/期限/監査/実験、secret storeとaccess。[coverage.json](coverage.json) に具体的な問い、次の4実験、公式locatorを対応させる。外部provider/SDK、OS/global env変更、system config変更、実クラウド接続、現実のSLA・feature実験効果は未実行。

一次資料: [Python Truth Value Testing](https://docs.python.org/3/library/stdtypes.html#truth-value-testing)、[json conversion](https://docs.python.org/3/library/json.html)、[hashlib SHA256](https://docs.python.org/3/library/hashlib.html)、[OpenFeature Flag Evaluation API](https://openfeature.dev/specification/sections/flag-evaluation/)。[sources.json](sources.json) にlocatorと確認日を保存。OpenFeatureの資料はtyped evaluation/detail/errorを学ぶ参照で、SDK/provider準拠の認定ではない。
