# anchorと翻訳revision

file存在だけでは、fragmentの参照先や翻訳metadataの鮮度は確認できません。専有tmpに合成api.html、ja.html、guide.html、manifest.jsonを生成し、実byte read、UTF-8 decode、HTMLParserでのid/href抽出を実行します。各本文・SHA256・UTC/runtime・fixture・source binding・tmp cleanupを原票に残します。

前提はHTML id/hrefとfragment、revision。元の文書生成/鮮度教材から、anchorと翻訳revisionへ進む有限続編です。次候補はSphinx実buildの参照警告とpo/pot更新検証で、未制作です。

| 条件 | anchor一致数 | ja sourceRevision / en revision | strict結果 |
| --- | --- | --- | --- |
| normal | 1 | 2 / 2 | PASSED |
| broken-fragment | 0 | 2 / 2 | BROKEN_ANCHOR |
| duplicate-id | 2 | 2 / 2 | AMBIGUOUS_ANCHOR |
| stale-translation | 1 | 1 / 2 | STALE_TRANSLATION |

bad-broken / bad-duplicate / bad-staleはfile-only故障です。観測traceは残し、pass決定だけfile存在に置き換え、各ケースをBAD_PASSEDとして誤passします。翻訳自身のrevisionは2でも、参照した元revisionが1なら古いと判定します。HTML本文に書かれたrevision文字列の意味や翻訳文の正しさは検査しません。

[事前literal表](hand-oracle.json)はproducer初回実行前に作成済みです。[oracle.py](oracle.py)はその表のみ読み、HTMLParser/validatorを共有しません。[check.py](check.py)は全field、実本文/読取digest、source binding、cleanupを照合し、欠落pass・重複一意化・古い翻訳fresh・故障safe・外部URL許可・cleanup偽装の6mutantを拒否します。INPUT_REJECTEDは意図したsubset拒否、EXECUTION_FAILUREはoracle未判定であり、正常一致の件数に混ぜません。

入力UIは10個の固定合成fixtureだけです。固定page名、固定manifest形、単一guideリンク、対象api.html#fragmentに限定します。HTMLParserの許可tagはhtml/body/h1/h2/p/a、属性id/href、閉じtag順を検査する独自subsetです。任意manifest/HTMLの一般validatorではありません。外部URL、../path、iframeは拒否し、URLをfetchしたり範囲外fileを読んだりしません。IDの一意性は対象document内のfragment一致数で判断し、ja.htmlに同名idがあること自体は重複扱いしません。

[Sphinx cross-reference](https://www.sphinx-doc.org/en/master/usage/referencing.html#cross-referencing-arbitrary-locations)はlabelと参照警告の文脈です。Sphinx labelのdocumentation全体の一意性とは範囲が違います。[Sphinx translation updates](https://www.sphinx-doc.org/en/master/usage/advanced/intl.html#update-your-po-files-by-new-pot-files)は元文書更新時のpo/pot更新の文脈です。本教材は独自manifest契約で、Sphinx buildや翻訳内容の正しさを実証しません。

原票は[raw.json](observations/20261005T155132255313Z/raw.json)、[画面観測](observations/iab.json)、[合成失敗](observations/failure-qa.json)、[実遅延応答破棄](observations/held-qa.json)、[cleanup](observations/cleanup.json)、[検証receipt](observations/verification.json)。画面captureはツール上で表示確認しましたが、保存fileはありません。

~~~sh
python3 -B check.py
python3 -B route.py anchor-and-translation-revision
python3 -B route.py unsupported
~~~

最後はexit2で無変更。通常再読はread-onlyです。新しい原票が必要な場合だけpython3 -B runner.py --recordで新UTCディレクトリに記録します。プレビューはpython3 -B server.pyが専用127.0.0.1動的portを表示します。終了時はそのプロセスだけを止めます。

画面は予測→条件→実parse→比較→source/raw→実結果から生成する答えの順です。予測変更は新値と他予測を保持し旧答え本文を空にして閉じます。条件変更は全予測unknown。合成return failureとHTTP503は旧比較を消してoracle未判定、保留した実応答はgeneration変更後に実送信しても表示を復活させません。

標準Pythonのみ、全入力synthetic、専有tmpのみ。既存Subject/Portal/Core/fullGate、他教材、host設定、公開サイト、install/commit/pushは対象外です。全Subject/Atlas完了の宣言はしません。
