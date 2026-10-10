# State ownership: 同じentityをlist/detailへ表示する

2entityの保存データを、値copyの二所有とID参照の一所有で比較するnative Browser教材です。React/Reduxはconceptの一次資料で、実行した製品ではありません。Subject全体の完成ではなく、実network/persistence/SSR/routingも扱いません。

## 学習の道筋と実務判断

前提はobject/array、ID、コピーと参照、関数、DOMのtextContent。identity→保存データの所有者→派生表示→selectionのID→更新/削除の不変条件を、予想→操作→異常比較→図/実装/原典→回答で学びます。

保存名をOrbitへ編集すると、detail copyだけ更新する意図的な不十分設計ではlist Alpha/detail Orbitになります。normalized版はbyIdを一箇所更新し、IDからlist/detailをderiveするため両方Orbitです。選択をbへ移してもaのcopy差分は残ります。削除はids/byId/選択を合わせ、unknownID・空白だけ・25文字・未選択は拒否します。24文字を受理する境界も比較します。文字数はtrim後のUTF-16 code unitsで、ユーザー知覚文字数/全validationの保証ではありません。

実務では「同じ保存データの更新責任を一箇所へ寄せる」「UI選択はentity自体でなくIDにする」「表示は保存stateからderive」「削除後の参照を整理する」と判断できます。一方、未保存draft/取消/履歴用copyは保存データと別概念で、copyやlocal stateを全て廃止する話ではありません。正規化だけでnetwork競合/権限/あらゆる表示不具合は防げず、全stateをglobalに置く必要もありません。

## 所有と表示の図

```text
値copy版（意図的なdetail-only保存）     normalized版
listItems ──────────> list            ids ──┐
detailById ─────────> detail          byId ─┼──> derived list
selectedId ─────────> detail選択      selectedId ─> derived detail
 ↑同じentityの保存値が二箇所            ↑保存entityの所有者は一箇所
```

[UIの図と現在state](index.html#ownership-diagram)を操作前後に読みます。両modelの選択IDは同じ入力で変更。DOMは明示的render()で更新し、frameworkのsubscriptionを実装/検証していません。rawはstate/view/event/inputで、OS/Network全traceではありません。

## 起動・操作・検査

このdirectoryで、依存追加なしに実行します。

```sh
node verify.mjs
node check.mjs
node serve.mjs
```

verifyはNodeでpure modelを固定oracleへ照合。checkは保存Browser原票と実DOM/入力event/現在Sourceを独立照合します。Node成功だけではBrowser UIの証拠になりません。serverはown 127.0.0.1:port0を表示。そのURL/title/操作欄を確認して開き、終了はCtrl+Cで自分のserverだけ停止。

1. detail copy更新時のlistを予想して保存。
2. aの保存名Orbit→空白（拒否）→`abcdefghijklmnopqrstuvwx`（24受理）→同文字列+y（25拒否）。
3. bへ選択しSignalへ編集。ghost選択・unknown編集/削除は拒否。
4. b削除→未選択削除拒否→a選択/削除→削除済a選択拒否→未選択編集拒否。
5. 初期化して両modelを戻す。eventは消さず、reset入力として残す。
6. 図/[model](model.mjs)/[独立oracle](oracle.mjs)/原典へ戻り、回答3候補を比較。

通常checkerはread-only。新しい原票が必要な場合だけ、未使用directoryへ明示保存します。

```sh
node verify.mjs --record new-node-01
node check.mjs --record new-check-01
```

既存directoryは拒否し成功/失敗原票を上書きしません。Browser新規実測は別の実Browser操作が必要で、hashだけ変更して既存実行を新sourceへ再bindingしません。

## 原典と独立期待値

[React Choosing the State Structure](https://react.dev/learn/choosing-the-state-structure)、[Redux Normalizing State Shape](https://redux.js.org/usage/structuring-reducers/normalizing-state-shape)、[Redux Deriving Data with Selectors](https://redux.js.org/usage/deriving-data-selectors)を2026-10-05に確認。重複する情報/ID/派生のconceptから独自fixtureを作り、公式のサンプルコード/画面はコピーしていません。URLは生きた公式文書のlocatorで、全本文のdigest固定/全知識網羅はしていません。

oracleはmodel/selector/DOMをimportせず、17状態の入力・保存state・表示・拒否理由を固定。modelから期待値を作りません。Browser checkerはvalue copyの不整合も「期待する意図異常」として残し、成功へ隠しません。

## 主要未教材coverage → 次の4実験

[scope.json](scope.json)の非網羅の主要8領域に対する入口です。全て未実装の計画で、今回の実行Evidenceではありません。[index](index.html#learning-path)にも同じ導線があります。

| 計画 | 領域・具体的な問い | 次の実験と公式locator |
|---|---|---|
| E1 境界とcomposition | boundaries-dependencies / framework-composition。feature/component間の更新責任・依存方向・通知はどこへ？ | list/detailをreducer/contextへ分割しcleanup/更新経路を比較。[React Reducer and Context](https://react.dev/learn/scaling-up-with-reducer-and-context)。全framework/API設計は別途。 |
| E2 selectionとdraft | routing-navigation / forms-drafts。URL/履歴/取消で選択・未保存入力はどう変わる？ | URL選択とdraft保存/取消を分けidentity/resetを比較。[React Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state)。routing製品/undo/mergeは未教材。 |
| E3 外部stateと版 | async-server-state / persistence-migration。保存失敗/再取得/offline/schema更新時の正本は？ | 承認済み別fixtureでNetwork/保存/版移行を比較し責任を図示。[Redux Side Effects](https://redux.js.org/usage/side-effects-approaches)。今回のlocal編集とは別の実証。 |
| E4 SSRと品質 | ssr-hydration / quality-operations。server/client移行と回帰でview一致をどう確かめる？ | SSR mismatchと独立interaction oracleを比較しa11y/security/performance/運用へ広げる。[React hydrateRoot](https://react.dev/reference/react-dom/client/hydrateRoot)、[Redux Writing Tests](https://redux.js.org/usage/writing-tests)。全品質/運用Gateではない。 |

[検証記録](VERIFICATION.md) / [教材専用Skill](skills/atlas-frontend-application-architecture/SKILL.md)。独立Forward Eval、全Browser、実framework、外部サービス/production権限・操作は未実施。Docker、依存、OS/GitHub、global Skill、commit/push/公開は変更しません。
