# Platform engineering / developer experience：生成成功とcontract適合

Subjectの学習入口です。今回の有限教材はstdlibだけのtask-owned project template generatorとcontract validator。cedar/mapleの架空projectをmodule内の使い捨てfixture treeに生成します。全Subjectは未完成です。git init・外部repo・saved project・global install・実会社platformは作りません。

## 前提 → 主要概念と仕組み

前提はJSON、file tree、version、hashです。platformは利用者の作業を支える共通能力で、templateはその一部です。[CNCF Platforms White Paper](https://tag-app-delivery.cncf.io/whitepapers/platforms/)のplatform-as-productと、[Backstage Software Templates](https://backstage.io/docs/features/software-templates/)の入力→steps→結果を概念比較します。今回はBackstageを実行しません。

入力はname/owner/kind/schemaVersionの4key。nameはASCII小文字開始・最大20字、ownerはteam-a/b、kindはlibrary/worker、schemaVersionは整数2。省略・未知keyを拒否します。nameにpathを許さず、生成fileもresolve後のroot配下だけです。[JSON Schema object](https://json-schema.org/understanding-json-schema/reference/object)のrequired/additionalPropertiesと対応する小さな固定validatorであり、汎用JSON Schemaエンジンではありません。

current template v2はREADME.md、RUNBOOK.md、project.json、src/main.py。旧v1はRUNBOOKなしでtemplateVersion1。contractはcurrent v2の必要file、内容、schema/template versionを要求します。hashはbyte一致の観測で、品質・安全性・実行可能性の保証ではありません。src/main.pyは識別文字列だけで、生成projectを実行する教材ではありません。

## 予想 → 操作 → 正常・境界・意図異常の比較

「old-templateは2回同じhashならcontractにも適合するか」を予想して[UI](index.html)で操作してください。

```sh
python3 -B runner.py --case old-template
python3 -B server.py
```

serverの表示する127.0.0.1動的portを開きます。各操作はmodule observations/workの専用一時treeをfirst/repeatへrenderし、実fileを再readして比較。自分の一時treeだけ終了時に掃除します。既存projectのpathは受け付けません。

|case|理解する比較|
|---|---|
|cedar / maple|2neutral project、各4file。first/repeatのhashが一致しcontract valid|
|one-letter|name最小1字の境界。valid|
|invalid-config / path-escape|owner欠落 / ../outside。書込み0で拒否|
|old-template|決定的でもRUNBOOK欠落＋project.json変更＋templateVersion drift|
|schema-drift|schemaVersion1を実fileへ注入、project.json変更＋schema drift|
|tampered-file|READMEへDRIFT行追加、byte/hash差分|
|missing-file / extra-file|src/main.py削除 / extra.txt追加、必要/余分fileを比較|

## 原典 → 実装 → 答え

[templates](templates.json) → [runner](runner.py)のrender/write/read/validate → [contract](contract.json) → [独立oracle](oracle.py)の固定期待treeを読みます。oracleはrunner/templates/contractを読まず、cedar/maple/aの正しい全file文字列と意図異常treeを手書きしています。答えは「決定的な生成でもold-templateはcurrent contractへ不適合」です。生成が終わったことと利用者が必要なfileを得たことを分けて確認できます。

[Path.resolve](https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve)のsymlink解決も読みます。専用rootでpath escape候補を検査しますが、TOCTOUや悪意ある同時書込みへの保護は実証しません。

```sh
python3 -B checker.py --record  # 明示更新：実render原票とfixture artifact
python3 -B checker.py           # 保存原票・hash・独立oracle・QAのread-only検査
```

[実行原票](observations/run.json)、[QA](observations/qa.json)、[session](observations/session.json)、[一次資料locator/binding](sources.json)、[module skill](skills/atlas-platform-engineering-developer-experience/SKILL.md)。原票は実UTC/環境/input/raw/source/artifact digestとdiffを保存します。通常checkerはrenderやartifact更新をしません。recordは自身の保存fixtureを置換します。

## 実務判断 → 限界 → 次に学ぶ

今回判断できるのは入力の適合、生成byteの再現性、current contractとの差分と拒否時の書込み0です。実務ではtemplate更新時に必要fileとversionの移行をレビューする視点を学べます。開発者の認知負荷、導入効果、platformの成功はまだ測れません。

固定2kind/2owner・text fileだけ。generated sourceの実行、依存解決、認証認可、catalog統合、セルフサービスworkflow、移行の安全性、実組織DXは未実証です。

|未教材coverage・問い|次の実験（未実施）|公式locator|
|---|---|---|
|Platform as product / DX：誰のどの待ち時間を減らすか|架空2personaで手作業とtemplate操作のsteps/待ち/エラー回復を比較。満足度と速度を混同しない|[CNCF Platforms](https://tag-app-delivery.cncf.io/whitepapers/platforms/)、[DORA platform engineering](https://dora.dev/capabilities/platform-engineering/)|
|Self-service / policy：誰がどのactionを選べるか|架空role別に生成/登録の許可を評価し、拒否時artifact無しを確認|[Scaffolder authorization](https://backstage.io/docs/features/software-templates/authorizing-scaffolder-template-details/)|
|Catalog / ownership：生成物のownerと依存は追えるか|fixture descriptorの参照切れ・owner欠落・変更を比較|[Catalog descriptor](https://backstage.io/docs/features/software-catalog/descriptor-format)|
|Golden path lifecycle：更新とescape hatchは両立するか|v1→v2 migrationのdiffと手編集保持・再生成衝突を比較。generated source実行は別教材|[Software Templates](https://backstage.io/docs/features/software-templates/)、[JSON Schema object](https://json-schema.org/understanding-json-schema/reference/object)|
