# Linux Desktop Platform Engineering

Desktop Entryの有限parserをこのMacのPython標準ライブラリで実行する教材。[index.html](index.html) は予想→操作→trace/argv比較→原典/実装→答え。Execは文字列としてだけ処理し、processやshellを起動しない。Linux GUI・X11/Waylandの動作は未実証。

## 学習の道筋

1. 前提: `.desktop`、group/key、string、argument、field codeを知る。
2. 主要概念: string escape解除、whole argument引用解除、単一field展開を区別する。構文、launch方針、GUI表示の責務も区別する。
3. 今回の実装: [fixtures.json](fixtures.json) の27entry × 5合成file選択を [model.py](model.py) で解析。groups、tokens、各段階のtrace、argv配列を実際に生成する。正しい有限parserと置換後単純splitのbadを比較する。
4. 正常/境界/異常: 引用された固定argument、空argument、二段escape、空白/日本語/%を含むfile、0/3file、未知code、重複code/key、閉じないquote、shell要求を比較する。
5. 実務判断: 構文からargument境界を判断できる。parser成功だけではアプリ存在、許可、activation、window表示を判断できない。
6. 限界と原典: 以下のsubsetと未教材coverageを読み、原典へ戻る。全Subject完成ではない。

## 実行

このディレクトリで実行する。入力も全て合成値。

```sh
python3 -B run.py
python3 -B run.py --case single --selection spaces
python3 -B run.py --case dollar --selection max
python3 -B run.py --case unknown
python3 -B run.py --launch shell
python3 -B check.py
python3 -B server.py
```

正常CLI exit0、解析拒否/未対応CLI exit2。serverのtemporary127.0.0.1 URLを開く。APIはcase/selection/launchを各1つだけ受け取り、既知fixtureの解析拒否もHTTP200の実験結果、未知fixture/queryはHTTP400。UIは実行開始時に前回結果を消す。所有serverをCtrl-Cで終了。通常checkerはread-only。原票更新を指示した場合だけ `python3 -B check.py --record`。

## 原典と有限subset

- [Basic format](https://specifications.freedesktop.org/desktop-entry/latest/basic-format.html): Desktop Entryが最初、重複group/keyを拒否。コメントと未知keyはraw入力/groupsへ保持。書き換え機能はない。
- [Value types](https://specifications.freedesktop.org/desktop-entry/latest/value-types.html): string escape `\s` / `\n` / `\t` / `\r` / `\\` を第一段で解除。Exec rawはprintable ASCII。
- [Exec key](https://specifications.freedesktop.org/desktop-entry/latest/exec-variables.html): 第二段でwhole quotingを解除、その後fieldを1回だけ展開。実装はstandalone `%f` / `%F` と未引用 `%%` に限定する。未知codeはinvalid、既知の他code・引用field・embedded `%f` はsubset未対応として拒否。quoted fieldの結果は原典でundefined。引用された `;` / `|` はliteral文字として保持する。
- [Recognized keys](https://specifications.freedesktop.org/desktop-entry/latest/recognized-keys.html): Type=Application、非空NameとExecを要求。Terminal/DBusActivatable=trueは未対応。booleanはtrue/false。表示や起動を変えるPath/TryExec/Hidden/NoDisplay/OnlyShowIn/NotShowIn/Actionsも未対応で拒否する。

これは全仕様validatorではない。localization key、追加groupの意味、deprecated code除去、URL、Icon、Name展開は未実装。追加groupは構文保持のみ。任意の未知keyを起動条件として解釈しない。quoted %%も本subsetでは拒否する。quoted CR、unquoted tab等は対応外。Nameのescape/localization検証も範囲外。

教材policyとして実行名は `atlas-viewer`、`/synthetic/bin/atlas-viewer`、`/synthetic/My Apps/atlas-viewer` だけを受理。存在確認しない。`sh`等はpolicy拒否する。この許可表はDesktop Entry仕様自体の制限ではない。entry最大2048文字、fileは0–3件、`/synthetic/` 始まり・最大128文字・制御文字なし。これも教材の有限境界でOS quotaではない。後段へ渡すargvをmodel化するだけで、PATH検索、shell、install、GUI実行はない。

## 手token oracleと手計算

[oracle.py](oracle.py) はmodelをimportせず、原文をparseしない。別に手で定義した12正常fixtureのtokens・quote属性、15拒否fixtureの分類から期待argvを計算する。file選択も別定義し照合する。test対象と同じtokenizerを再利用しない。

| 条件 | 期待 | 判断 |
|---|---|---|
| quoted / spaces | `["atlas-viewer","--label=two words","/synthetic/two words.txt","/synthetic/b.txt"]` | 固定argumentとfile名の空白を分割しない |
| single / spaces | fileごとに2つのargv配列 | `%f`で複数fileを渡すとき、このモデルは1fileずつ。原典の複数起動推奨を選択したmodel方針で、実launcherの挙動は未測定 |
| empty-arg / none | `["atlas-viewer",""]` | 空argumentを保持しfile fieldを除去 |
| percent / percent-name | `--progress=100%` と `/synthetic/%F.txt` | %%だけliteralへ。置換文字列を再展開しない |

badはraw文字列のfield置換後にsplitする意図異常。引用解除をせず空argument/空白fileを壊し、%fの複数launchを表せない。badも起動しない。checkerは3つのbad反例と再帰field展開の意図故障を検出する。合成「quoted semicolon」を実行して安全性を試すことはしない。

## 原票と検証

[evidence/run.json](evidence/run.json) は実行時刻、Python/OS環境、135条件の原文/input digest、実parse trace/raw digest、argv、独立期待、境界/故障結果、公式locator。[bindings](evidence/bindings.json) はsource/artifact SHA256とlocatorを結ぶ。[UI QA](evidence/ui-qa.json) は実IAB操作・観測とcapture保存可否、所有server/tabの終了。[routing smoke](evidence/routing-smoke.json) と [Skill](skills/atlas-linux-desktop-platform-engineering/SKILL.md) は既存コマンドへのrouteを確認する。主agentのsmokeであり独立forwardAgentEvalではない。

通常checkerは原票と内容を照合し、README/indexのroadmap・公式locator・README local linksも確認する。原票生成前はREADME local linksの未生成evidenceだけをbootstrapで許容する。Core `atlas audit` / `npm run gate` は専用module scope外で未実行。全Subject完成は主張しない。新Goalは作成しない。

## 未教材coverageと次の実験

| 主要概念・問い | 次の実験 | 公式locator |
|---|---|---|
| discovery/config: XDG優先順位、同名entry、Hidden、localizationは | 合成user/system directory集合でoverrideとvisibility比較 | [XDG Base Directory](https://specifications.freedesktop.org/basedir/latest/) / [entry keys](https://specifications.freedesktop.org/desktop-entry/latest/recognized-keys.html) |
| integration: MIME/URL、%u/%U、D-Bus activation、単一instanceは | 合成MIME選択とActivate/Open message model比較 | [D-Bus Activation](https://specifications.freedesktop.org/desktop-entry/latest/dbus.html) / [MIME registration](https://specifications.freedesktop.org/desktop-entry/latest/mime-types.html) |
| display/session: X11とWaylandのwindow、input、buffer、compositorは | 合成client→surface→compositorの状態遷移と未応答比較 | [Wayland architecture](https://wayland.freedesktop.org/docs/book/Introduction.html) |
| delivery/operations: install、launch policy、TryExec、sandbox、packagingは | 合成executable inventory・許可表とpackage entryの一致/欠落を検査 | [TryExec/Path/Terminal](https://specifications.freedesktop.org/desktop-entry/latest/recognized-keys.html) |

以上は未教材。今回のargument境界を理解した後は「どのentryが選ばれ、どうactivationされ、どのsessionへwindowが出るか」を追う。実Linux session、D-Bus、MIME database、PATH、filesystem install、sandbox enforcement、GUI起動は検証していない。
