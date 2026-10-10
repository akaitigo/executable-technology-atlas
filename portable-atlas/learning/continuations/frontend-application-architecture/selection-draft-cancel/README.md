# selectionと未保存draft: bの取消でa編集も消える？

[元Subject E2](../../../subjects/frontend-application-architecture/README.md#主要未教材coverage--次の4実験)のselection/draftへ進む追加単元。正本をIDで一所有にする前教材から、未保存draftとURL選択、取消/保存の責務を分ける。実vanilla JSをBrowserで操作し、Reactはconcept原典だけ。

読む順番は前提→保持契約→2予想→編集/切替/取消/保存/戻る→正常と共有draft故障→実DOM/URL/raw・独立表→答え/実務判断。前提はID付きobject、DOM input、URL、未保存入力。[process contextのreset修正](../../observability-engineering/process-context-propagation/README.md)と同じく、予想だけを変更しても旧比較を消し、新予想を保持する。

独自契約はa=Alpha/b=Beta、選択a/b、textはtrim後UTF-16 units1..40。draftはID別に切替後も保持し、cancelは対象IDだけを消し正本表示へ戻す。saveだけ対象canonicalを書き換える。未編集saveはNO_DRAFT、unknown ID/blankは拒否して正本/selectionを変えない。今回の判定は知覚文字数や全validationの保証ではない。[事前期待](EXPECTATIONS.md)と[手書き状態表](oracle.json)を実Browser操作前に固定。

| 同じ操作 | 正常ID別draft | 単一shared draft故障 |
|---|---|---|
| aをAlpha draftへ編集 | canonical a=Alphaのまま | 同じ |
| bへ選択・URL id=b | b表示Beta | a draftをbへ流用 |
| b取消→own browser Backでa | a draft保持 | a draftまで消失 |
| a保存 | aだけAlpha draftへ | NO_DRAFT拒否、aはAlpha |
| 取消せずb保存する別列 | NO_DRAFT拒否 | b canonicalへa draftを誤保存 |

[UI](index.html)は実modelを編集する。状態操作後、条件変更、各予想欄の単独変更は旧比較/答えを消す。条件は正本/draft/selectionと予想を初期化、予想変更は新値と他欄を保持する。拒否時は予想と実理由を比較できる。実Error注入はEXECUTION_FAILUREを記録し、正常答えを出さず初期化まで失敗を保持する。

[app.js](app.js)は正本とdraft/selectionを別に持つ。実input/select/save/cancel/popstateイベントの後、stateとURLをlogへ保存。Browser原票ではlogだけでなく独立DOM read（input.value、正本table、選択heading、draft表示、実URL）を採取し[oracle](oracle.py)へ照合。正常/faultの各操作列は新しい所有tabで実行し、a→bの1entryだけ実Backする。初期URL id=bからbを選択する別caseも確認する。

URLは選択のみで、draft/正本の永続化ではない。条件reset前のhistory entryはgeneration不一致でSTALE_HISTORY拒否しcurrent URLへ戻す（全router仕様ではない）。fresh loadはfixture正本へ戻るのでreload保存を保証しない。faultの予測どおりの観測は検算PASSでも正常設計のPASSではない。

```sh
python3 -B preview.py                 # 自分のdynamic127.0.0.1 server
python3 -B record.py                  # 保存rawをread-onlyで読む
python3 -B checker.py                 # producer非importのID表/実DOM/URL/source照合
python3 -B route.py draft
python3 -B route.py react             # unsupported exit2
python3 -B record.py --record --input OWNED_IAB_CAPTURE.json
python3 -B checker.py --record-binding
```

明示recordは実IAB入力をunique新rawへ保存する。通常checker/routeはBrowserを操作せず証拠を生成しない。sourceを変えたら新Browser観測が必要で、古い原票のhashだけを更新しない。失敗観測も保存し、unexpected execution failure入力はcurrentへ昇格させない。toolが作る原票と実行側の失敗表現を分離する。

答え: 選択IDを変えてもdraftの所属IDを変えない。cancel/saveは現在IDへの作用で、b cancelがa draftを消したりb saveがa draftを保存したら境界が壊れている。正本copyの二所有を避ける話と、独立した未保存copyを持つ話を区別する。

実務判断: 保持/破棄の方針を明示し、編集・切替・戻る・取消・保存を同じ列で検査する。保存前canonical不変、対象IDだけsave、取消が他IDへ波及しないことを状態とDOMで照合する。componentのkey変更だけで外部保存/mergeまで解決したと判断しない。

coverage増分はID別draft、取消/保存、own URL/history。次の3実験（未実施）:

1. 外部保存失敗→再取得でcanonical/draft/版を分離。[元Subject E3](../../../subjects/frontend-application-architecture/README.md)
2. React実component/keyでreset/保持を同じfixtureへ比較。[React原典](https://react.dev/learn/preserving-and-resetting-state)
3. 別entityの同時編集とundo/merge方針を新契約で比較。[元Subject E2](../../../subjects/frontend-application-architecture/README.md)

限界: vanilla JS・2ID・固定text・所有IAB tab、in-memoryのみ。React runtime/製品router/network/外部保存/reload保証/undo/merge/全Browser/a11y/performanceは未実証。Core/fullGate/Portal/他教材/install/設定/commit/push/公開は変更しない。

[原典](SOURCES.md) · [fixture](fixture.json) · [current raw](evidence/current.json) · [binding](evidence/binding.json) · [実IAB QA](evidence/ui-qa.json) · [検証](evidence/verification.json) · [限定Skill](skills/atlas-selection-draft/SKILL.md)
