# Atlas｜内容が同じでも、来歴の申告を許可できる？

[内容と独立baseline](related.html?topic=digest)→[推移material](related.html?topic=closure)→[今回の画面](index.html)の順で読みます。[元の学習経路](related.html?topic=path)の実験1、目標51に対応します。

全条件でartifactは同じ3byteです。それでも、別のbuilder、source、buildType、parameterの申告を同じpolicyで許可できるとは限りません。今回の問いは内容のhashの再説明ではなく、何を期待し、その期待を誰から受け取るかです。

条件と予想を選び、六つの照合項目を読みます。「別builder」と「同梱policyも差替え」はclaimsが同じです。正常版は別保持の期待で同じ不一致を返し、故障版だけが受信policyに合わせて一致扱いを変えます。

一致は署名や生成者認証の成功ではありません。この教材は独自形式のunsigned JSONを比べる有限模型で、実buildやreleaseをしません。[契約](CONTRACT.md)と[実装前手期待](expected.json)、[原典対応](SOURCES.md)、[Skill](SKILL.md)へ戻れます。

既存Pythonで7条件14応答を1回計算し、[保存結果](observations/run-01/results.json)を固定手表へ照合しました。作者189照合・8つのメモリ内改変拒否が通っています。画面はこの保存結果だけを再生します。独立担当も556関係と7改変拒否を照合しました（作者の件数とは合算しません）。7条件の全表示、10の切替状態、取得失敗・古い応答の5対照、1280/390pxの9実画面を確認しました。[再現手順](REPRODUCE.md)と最終受入の[確認状態](qa/reader-acceptance.json)、[残る不足](COVERAGE.md)を確認してください。
