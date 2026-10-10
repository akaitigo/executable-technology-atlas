# State ownership教材の検証記録

## 問いと期待値

2viewが同じ保存entityの値を持つとき、値copyの二所有とID参照の一所有で何が違うか。native実装の正常/意図異常/境界を比較し、React/Redux製品の動作実証とは呼びません。

17状態の固定transition oracleはinitial→edit-a→invalid-empty→boundary24-a→invalid25→select-b→edit-b→unknown-select/edit/remove→remove-b→remove-no-selection→select-a→remove-a→select-deleted-a→edit-no-selection→reset。copyのlistは元のAlpha/Beta、detailは編集値。normalizedのlist/detailは一つの保存値を参照。削除後はnull selection、全削除では両listが空、拒否時は保存stateを維持します。resetもeventとして記録し、過去eventを消しません。

## 経路・証拠の区別

Node verifyはpure modelを実行。Browser checkは保存原票のstate/view・実DOM・入力とbefore/after/outcome・Sourceを固定oracleへ照合します。NodeだけではDOMは確認できません。図はstate/data flow、イベントはdomain instrumentationで、OS/Network全traceではありません。README/indexの4未実装案は主要8未教材領域へ接続し、全分野完成とは区別します。

## 実QA原票

2026-10-05 15:31:03.100–15:33:00.390 JSTに背景IABで操作した[Browser原票](observations/browser-attempt-01/browser.json)を保存しました。17状態それぞれに実DOM文字列、保存state/derived view、domain input/eventのbefore/after/outcome、Source binding、DOM snapshot、取得時刻を記録。予想、3回答、展開した学習案4rowもあります。環境はUA `Chrome/154.0.0.0` / Macintosh、ja、1280×720です。保存時刻と各domain eventの実行時刻は分けて残します。

[Node原票](observations/node-attempt-01/node.json)は15:29:27.014–15:29:27.017 JST、Node v25.2.1 / darwin / arm64。pure model 17状態・77項目（元state非破壊と3追加拒否を含む）が成功。[Browser原票の独立checker](observations/check-attempt-01/check.json)は285項目が成功し、copy差分隠蔽/古いnormalized list/unknown受理/dangling選択/偽Source/入力trace欠落の6改変負例を拒否。8未教材ID→4計画row、HTML local link8件も確認しました。合成改変負例は実Browserでそのバグを起こした証拠ではありません。

| 原票/実画面 | SHA-256 |
|---|---|
| Browser原票 | `f1024fd4ab209216fbdd3e0e08fb57af4aa830106b1eba22b402513872d2f2e3` |
| Node原票 | `9000fc7d4bf15958983d81097b03879de4224ddb1ea9b3d333d64cdc58013f1d` |
| [値が読める不整合画面](observations/browser-attempt-01/state-drift-visible.jpg) | `c729de180b471e4b67bb4212974f121a224b061ee4902839ae3c276b9479eade` |
| [空集合/未選択画面](observations/browser-attempt-01/empty-boundary.jpg) | `991acb43c6f10b18c9494b3dc561c21b9ae776331f509bfe2055b38caa7a53c4` |
| [所有の図の実表示](observations/browser-attempt-01/ownership-diagram.jpg) | `131a9c0d619decfbb6acf7b4e4305e5cddf1795030953c9a5599f1e1a2df4c4e` |
| [未実装学習案](observations/browser-attempt-01/roadmap.jpg) | `7e5cd0375f690faf4684a16b87d58ee718b792e7925e395d1fa52e490e336527` |
| 独立checker原票 | `9461f12b8412c502cdcd9cab514f4285453d8f1e5773c05e05525937642cd871` |
| [同一AgentのSkill確認](observations/skill-control.json) | `f729b2a1055797721f46b63cdad6d795003cb60069881ff49a2f16185956ef4c` |

Source9ファイルとchecker自身のdigestはchecker原票へ固定。画像は無加工JPEG、1280×720の実viewport抜粋。初回[state-drift.jpg](observations/browser-attempt-01/state-drift.jpg)は操作欄中心で値部分が見切れたため保持し、同じstateでdetailへscrollして追加のvisible画像を採用しました。長いroadmapの全表は一枚に収まらず、保存DOM snapshot/4rowで全体を確認します。所有図は独自の説明図をBrowserで表示した実画面であり、framework traceや外部実装の画面ではありません。

## 失敗保持・read-only・Skill・後片付け

初回recordはobservations親不在でENOENT/exit1。[失敗抜粋](observations/record-failure-01.json)は私的絶対path/stackを除き、error/command/原因を保持（正確な実行時刻は未記録）。明示record時だけ親directoryを作るよう修正して実modelを再実行し、Node原票を新規取得しました。通常検査ではdirectoryを作りません。

15:34:21 JSTの通常verify/checkはexit0。両既存directoryへ明示recordを試す負例はexit1/EEXISTで拒否され、前後で教材内22ファイルの全hashが不変でした。空/25文字/unknown/未選択拒否はBrowserでも実操作済みです。

教材専用Skillのquick_validateは成功。同一Agentの通常routeはreset後aをOrbitへ保存し、copy不整合/normalized一致を実UIで確認。対象外の実framework/network/persistence/SSR/routing保証はscope/未実装学習案へ案内し、新実装を追加していません。独立Forward Evalは未実施。

初回sandbox内listenはEPERM。一時loopback配信のみ許可された実行で起動し、OS/永続権限は変更しませんでした。own tab9を閉じ、127.0.0.1:50096のown serverをCtrl+Cで停止（exit130）。lsofでlistenerなし（exit1）を確認。他taskのtab/processを停止していません。

この専用directory以外、Root文書/Core/Graph/旧Goal/他Subjectを変更していません。Docker、依存、OS/GitHub設定、global Skill、commit/push/公開、新Goalもありません。Portal/Core全体Gateは未実行で、この有限教材をSubject/全体Goalの完成とは扱いません。
