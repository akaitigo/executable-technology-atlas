# Atlas｜field開示教材の範囲

目標73の「objectを読めることとfieldを返せること」を、有限の合成要求で比較します。元のsecurity-engineering READMEのproperty-level auth/最小開示という次実験に対応します。原担当の現在の稼働状況は正規APIで未確認のままです。担当を置き換えず、独立pathだけで制作しています。

| 内容 | 保存した根拠 | 限界 |
| --- | --- | --- |
| object許可とfield開示の分離 | 3role×3objectの省略要求9条件、field指定18条件 | この合成policyのみ |
| 既知の禁止field混在 | internal_noteとidの要求を全体拒否 | 一般の業務policyの正しさは保証しない |
| 未知role・未知field・role上書き等 | 境界12条件、拒否payload=null | 実認証・HTTP設計ではない |
| 将来fieldを暗黙開示しない | 1field追加で全7対許可3 | 任意のschema進化・nested fieldは未確認 |
| 入力・store不変 | 全40条件の前後比較 | DB副作用・同時変更は未実装 |
| 日本語の保存結果reader | 14項目、40条件の実DOM、202回の実操作、実画像9枚 | 保存された関数結果の説明で、実API操作ではない |
| 前提教材への導線 | 既存2資料への実リンク操作と本文全文一致 | 元の実験は再実行していない |

[画面確認](qa/run-2026-10-06T143811732Z/report.json)には条件・予想・resetの状態と、取得失敗・改変・古い応答の記録もあります。[作者の画像確認](qa/self-visual-review.json)と[独立受入の状態](qa/reader-acceptance.json)を分けて参照してください。古い応答はAbortを含む通常経路の確認で、任意の競合や世代番号だけの検証ではありません。

元のobject/operation/tenant/grantとconditional-read-toctouは既存の前提です。privacy匿名化、database効率上の射影と同一の受入として扱いません。作者の加算は0です。

次に残る主要な問いは、上流で信頼済みcontextを確立・失効させる認証/session、書込側のfield許可（mass assignment）、field policyとDB変更を含む整合性、nested fieldとschema変更です。この教材の受入はこれらを完了へ変えません。cryptography/TLS、供給網、入力sink防御、可用性、logging/incident、secure SDLC、AppSec全体も未完成です。

参照入口は [原典対応](SOURCES.md)、[初期条件](CONTRACT.md)、[実装前追補](CONTRACT-ADDENDUM.md)、[保存結果](observations/run-01/results.json) です。親の共有計画・受入台帳・旧repoは変更していません。
