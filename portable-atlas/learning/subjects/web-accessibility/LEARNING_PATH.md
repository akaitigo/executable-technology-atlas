# Web accessibilityを学ぶ道筋

この文書は[ボタン操作の既存教材](README.md)から、名前、focus、動的通知、表示条件へ進むための補足です。有限教材の補足であり、分野全体の学習完了やWCAG適合を示すものではありません。以下の次実験はすべて未実行です。

## 1. 前提と主要概念

HTML要素、DOM、event、focus、CSSの基本を押さえます。見える文字、DOM属性、computed accessible name、支援技術の読み上げを区別します。機能が同じでも、利用者がそこへ到達し、目的と状態を理解し、操作できる経路が異なります。

学ぶ順序は **native semantics → キーボード操作 → role/name/state → focusの移動と復帰 → フォーム・複合widget → 動的更新 → 視覚・入力条件 → 実支援技術と監査** です。

- clickできることはTabで到達できることを意味しません。roleやtabindexだけでもキー動作は自動実装されません。
- native要素を選ぶ判断と、custom widgetに必要な操作・状態・focusを実装する判断を分けます。
- accessible nameは計算規則の結果です。textContentや見た目だけで推測しません。
- Nodeのreducer検査、実Browserのtrusted入力、AX tree、実スクリーンリーダーの音声は異なる証拠です。

## 2. 予想から既存実測へ

[UI](index.html)でTab・Enter/Space・名前を予想し、[キー処理](keyboard.js)、[Browser原票](observations/browser-attempt-01/browser.json)、[Node境界原票](observations/node-attempt-02/node.json)、[観測監査](observations/audit-attempt-01/audit.json)、[検証記録](VERIFICATION.md)を読みます。この文書作成ではBrowserやNodeを実行していません。

| 条件 | 保存済み実測 | 外れる予想 |
|---|---|---|
| native button | Tab到達、Enter/Spaceで0→1→2、focus-visible | 特別なcustom処理が必須、とは限らない |
| click-only div | Tabで飛ばされ、mouseでは0→1 | 見た目とclickだけで操作経路は揃わない |
| role+tabindexだけ | 到達・role/nameあり、キーでは0のまま | roleがあればキー動作も備わる、は誤り |
| 修正版div | キーで0→1→2、focus保持 | 宣言したキー契約が機能する |
| disabled | nativeはTab順から外れ、customは到達するが作動しない | 全無効controlのfocus動作が同じ、とは限らない |
| 名前欠落と修正 | 空nameをrole queryで検出、修正後は指定name | 文字が見えれば名前もある、は誤り |

22観測・66期待値照合、fresh trusted入力・時刻・Tab遷移の監査が記録されています。これは対象Browser経路での測定です。Spaceのblur取消やrepeatはNodeの独立表でも検査されていますが、全Browser・物理長押し・全ATの証明ではありません。AXの空nameの根拠はrole queryとの併読で、画像や`button unnamed`表記だけではありません。

無効controlへのlocator入力がactionability待ちで停止した記録は、キーを送信して成功した扱いにしません。初期原票と部分checkpointも、最終観測の代替ではありません。実VoiceOver/NVDA/JAWS/Braille、mobile、WCAG全監査は未測定です。

## 3. 実務で何を判断するか

まず適切なnative要素を選び、操作対象に理解できる名前と状態を与えます。customにする場合は、focus、キー、disabled、repeat、取消を含む契約を明示します。フォームやdialogでは操作の前後にfocusがどこへ移るかも評価します。

自動・DOM検査に加えて、キーボードだけで目的を達成できるか、zoomや狭幅で情報が失われないか、対象ATで状態変化が伝わるかを確認します。Browser/OS/ATと入力方法を記録し、未検証の組合せを残します。APGは実装指針、Understandingは達成基準の解説として読み、教材単体のpassをWCAG適合宣言へ広げません。

## 4. 一次資料への道筋

| 原典とlocator | 読む目的 |
|---|---|
| [W3C APG Button Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/button/)、Keyboard Interaction / Roles, States, and Properties | Enter/Space、名前、状態、操作後focus |
| [AccName 1.2](https://www.w3.org/TR/accname-1.2/#computation-steps)、§4.2 / §4.3.2 | 名前と説明、hiddenと参照の計算。取得時は2026-10-02 Working Draft |
| [APG Modal Dialog](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)、Keyboard Interaction | 初期focus、Tab循環、Escape、閉じた後の復帰 |
| [WCAG 2.2 Understanding Focus Visible](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html)、Intent | キーボードfocusの可視性 |
| [Understanding Status Messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html)、Intent / Examples | focusを移さず状態更新を伝える条件 |
| [Understanding Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html)、Intent | zoom・狭幅で情報と機能を保持する判断 |

AccNameの公開最新版はdraftで、凍結されたRecommendationではありません。実Browserの計算結果と、draftの読解を分けます。

## 5. 未教材の問いと次実験

| 未教材 | 問い | 次の入口 |
|---|---|---|
| name/description・参照 | どの文字から名前と説明が算出されるか | 実験1 |
| dialog・focus復帰 | 開閉とTab/Shift+Tabで操作位置を保持できるか | 実験2 |
| live region・実AT | focusを動かさない更新が利用者へ伝わるか | 実験3 |
| zoom・reflow・focus表示 | 拡大や狭幅でも操作対象を見失わないか | 実験4 |
| 見出し・landmark・表・言語・読み順 | 内容構造を辿れるか | 別の構造教材が必要 |
| forms、combobox、tabs、menu、grid | 入力エラーや複合操作をどう伝えるか | 別widgetのAPG・実操作が必要 |
| contrast、forced colors、touch、音声入力、media | 多様な知覚・入力・時間条件を満たすか | 別の測定環境と原典が必要 |
| 全AT・WCAG監査・継続回帰 | 用途と対象範囲を定めた評価が揃うか | 単体教材では未評価 |

既存の未制作範囲は[scope.json](scope.json)にあります。

## 6. 次の実験案（4本、すべて未実行）

1. **名前と説明の参照行列を作る。** 新しい独立fixtureでvisible text、aria-label、aria-labelledby、aria-describedby、参照先hiddenの条件を一つずつ変えます。先に原典から期待するname/descriptionを表にし、実Browserのcomputed値と照合します。予想は見える文字・名前・説明が一致しない条件があることです。hiddenは一律に無視すると決めず、直接参照された条件を別にします。DOM、参照ID、computed値、Browser版を保存し、推測で値を埋めません。原典はAccName §4.2 / §4.3.2です。

2. **modal dialogのfocusを開閉で追う。** 独立fixtureに起動buttonとdialog内2controlを置き、初期focus、Tab/Shift+Tab、Escape、閉じた後の復帰を実キーで観測する計画です。予想はfocusが開いたdialog内に入り、閉じるまで外へ抜けず、閉じると適切な起点へ戻ることです。期待するactive elementの列を先に固定し、focus管理がない故障版と比較します。原典はAPG Dialogです。2controlでの成功を入れ子dialog、全Browser/AT、全WCAG適合へ広げません。

3. **status更新をDOMと実読み上げに分けて確認する。** 合成の保存完了表示についてlive regionなし・適切なstatus roleありを比較し、focus位置を変えずに更新します。予想はDOMの更新だけでは通知経路を保証できないことです。実施時にはBrowser/OS/スクリーンリーダーの版を固定し、操作順、DOM/AX、読み上げ内容と時刻を別記録にします。音声を取得できなければAT観測未完とし、role属性やAXだけで読み上げpassにしません。原典はUnderstanding Status Messagesです。

4. **reflowとfocus可視性を有限条件で比較する。** 独立した短いフォームを、通常幅、320 CSS px幅、拡大条件で比較し、全controlへTabで到達します。予想は固定幅の故障版でoverflowや情報欠落が起き、流動layout版では内容を辿れることです。viewport、zoom手段、実CSS幅、scroll寸法、focus枠、欠落内容を記録します。viewport縮小とBrowser zoomを同じ操作と呼ばず、2方向scrollが必要な例外コンテンツも分けます。原典はReflowとFocus Visibleです。contrastやforced colors、全適合監査は残ります。

## 7. 資料の取得・検証状況

2026-10-05に上記6つのW3C HTML本文を取得して参照箇所を確認しました。今回取得不能だったURLはありません。APG・Understanding・AccName draftの位置づけを区別し、第三者本文・図・code exampleは保存していません。

追加したのはこの文書だけです。Node、Browser、AT、server、checker、UI、global gateは実行せず、既存原票・検証記録・digestを更新していません。次実験の予想は新たな実測証拠ではありません。
