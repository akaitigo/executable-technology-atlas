# Atlas｜書込field許可と拒否時不変の範囲

目標73の主体別最小権限と拒否時副作用の検査、および前の[読取field教材](related.html?topic=read-field)の残不足に対応します。読取の開示許可を再制作せず、write grant・field許可・storeへの反映順を追加して比較します。作者は加算を行わず、旧repoへの統合はしていません。

| 内容 | 保存した根拠 | 限界 |
| --- | --- | --- |
| readとwriteの別grant | viewerのreadはあるがwriteを拒否 | 上流認証済みcontextは仮定 |
| 書込fieldの許可表 | 3role、正常4・禁止7条件 | 教材固有の業務ルール |
| 2つの欠陥対照 | 一括代入の禁止更新、途中検査の部分更新 | 実製品の脆弱性率ではない |
| 拒否時store全体不変 | 修正版の拒否20条件、対象外recordも比較 | 単一メモリ。DB・並行atomicityは未確認 |
| 正常時の最小変更 | 4条件の指定field以外は不変 | 任意のschema更新の保証ではない |
| 入力境界 | 未知field/role、role/tenant追加、整数値、空/list changes等 | 型・長さ・巨大入力の全境界ではない |
| 保存結果reader | 14項目、24要求/72応答の実DOM、230操作、実画像9枚 | 保存結果の表示であり、ライブ更新ではない |
| 前提資料とSkill | 既存2資料への実リンクと本文一致、固定3問の資料利用 | 一般Agent評価や未知質問への保証ではない |

[画面の操作記録](qa/run-2026-10-06T163439899Z/report.json)には12件の切替等状態、5件の失敗/古い応答の状態も保存しています。[作者目視](qa/self-visual-review.json)と[独立受入](qa/reader-acceptance.json)は別の記録です。古い応答はAbortを含む通常経路で確認し、世代番号単独や任意競合を保証しません。

全24条件は初期storeをリセットして実行したもので、連続要求やエラー後の運用回復を検証したものではありません。値長1〜80の端点、JSONの重複キーやnested field、store中の不正schemaは未実測です。

次に残る問いは、書込とfield policy変更を含むDB整合、同時更新・競合時のtransaction、途中障害とrollback、nested field/業務値の妥当性、上流認証/sessionの失効です。既存conditional-read-toctouの読取側競合は別の前提で、未教材扱いし直しません。

実認証/JWT/HTTP、分散強制、永続化、一般の安全認証やAppSec全体の完成は対象外です。[契約](CONTRACT.md)・[手書き期待](expected.json)・[保存結果](observations/run-01/results.json)・[原典](SOURCES.md)から根拠を確認できます。原担当の稼働状態は正規APIで未確認のままです。
