# entry優先順位：Hiddenをskipするとsystemが復活する

元[Exec解析教材](../../../subjects/linux-desktop-platform-engineering/README.md)のdiscovery/config次案を有限化します。Execのargument境界→本entry ID/優先順位/Hidden→未制作のactivation/MIME/D-Busの順に読みます。元Subject・旧unit・共有Portalは凍結、入口追加0、Subject/Atlas incompleteです。

## 予想→実read→比較→原典→答え

前提はfile/directory、entry ID、boolean。既存Mac Python stdlibのみです。

~~~sh
python3 -B server.py
~~~

動的127.0.0.1 URLを開き、優先source/可用件数/抑止を予想。条件を選んで実readを行い、候補順・存在・action、実file原文/digest、結果を比較。原典とsource/rawを読んで答えを開きます。答えはactual visited/source/count/suppression/reasonから生成します。予想変更は新値と他の予想を保持し、旧本文を空にして閉じます。条件変更はunknownへ。実行開始、実行失敗、遅着旧応答も旧比較を利用しません。所有serverだけCtrl+Cで終了。

## 固定fileと独自subset

[fixtures](fixtures.json)/[手計算表](hand-oracle.json)は実行前に固定。毎回専有TemporaryDirectoryを/private/tmpに作り、user/system各applications/org.example.Mock.desktopへfixture UTF-8 bytesを書き、resolverは存在確認とread_bytesを実行します。raw pathは専有rootからの相対pathだけで、absolute tmp/host pathを保存しません。finallyでそのtmpだけcleanupし、消滅を確認します。host XDG変数・既存entryは読まず変更しません。Python checker/routingもtmpを生成せず原票を読むだけです。

| 条件 | 訪問候補 | 優先source / 抑止 / 可用件数 |
| --- | --- | --- |
| user/system通常 | user | user / false / 1 |
| userなしsystem通常 | user→system | system / false / 1 |
| user Hidden=true/system通常 | user | user / true / 0 |
| 両なし | user→system | none / false / 0、NOT_FOUND |
| Hiddenをskipする故障 | user→system | system / false / 1、BAD_RESURRECTED |

selected_sourceは優先entryまたは抑止entryのsourceで、可用applicationや実menu表示を意味しません。Hiddenの抑止と両候補の不在は別statusです。Visible候補件数という語も実Linux menuを観測した意味ではなく、この有限resolverの可用entry数です。

許可IDはorg.example.Mock.desktopだけ。範囲外IDは探索前拒否（tmp fixture設置は行うが範囲外pathには書かない）。groupはDesktop Entryだけ、keyはType/Name/Exec/Hidden、Type=Application、非空Name、Exec=atlas-mock。Hiddenはtrue/false、欠落ならfalse。invalid-bool yes、duplicate-key、outside-idを独自subsetで拒否してsystemへfallbackしません。拒否は実行障害/不在と別扱い。原典の全parser/曖昧な無効上位entryへの各desktop対応を再現しません。コメント/space/escape/localization/他key・group・symlink・入れ子ID・複数systemrootは対応外。Execは文字列として読むだけで、process/shellは起動しません。

## 再現と独立検査

~~~sh
python3 -B runner.py --record
python3 -B check.py
python3 -B route.py entry-precedence-hidden-override
python3 -B route.py unsupported
~~~

--recordだけ新UTC folderへ実read原票を保存。既存原票は書き換えません。checker/routeはread-only、unsupportedはexit2。[oracle](oracle.py)はresolver/parserをimportせず、事前literal候補順/優先source/抑止/件数/拒否表を使います。checkerは実read raw/digest・fields/action、入力/source SHA、UTC/runtime、tmp cleanupも照合。8条件（選択2/抑止1/不在1/故障1/期待subset拒否3）、6mutant拒否です。

[検証receipt](observations/verification.json)が実IAB全条件/actual答え/control reset・専有fileの実UTF-8 decode失敗/合成HTTP503失敗・実遅着旧応答の破棄、所有tab/server終了、全file SHA/mtime不変へ接続。sandbox実bind errno1は保存し、同じowned localhost commandをhost permissionで起動。failure probeは専有fileへ制御したinvalid byte ffを書き、実read後のUnicodeDecodeErrorとcleanupを記録します。実Linux環境障害の証拠ではありません。合成HTTP503は実resolver障害と数えません。captureはtool実表示のみ、保存ファイルなし。[有限Skill](skills/atlas-entry-precedence-hidden-override/SKILL.md)は同一agent routingで、独立Forward Evalではありません。

## 原典・範囲・次案

2026-10-06 JSTに[XDG basedir §3](https://specifications.freedesktop.org/basedir/latest/)のDATA_HOME優先とDATA_DIRS順、[Desktop Entry §2.1 ID](https://specifications.freedesktop.org/desktop-entry/latest/file-naming.html)の同ID優先、[§6 Hidden](https://specifications.freedesktop.org/desktop-entry/latest/recognized-keys.html)のuser-level削除、[§3.3重複key](https://specifications.freedesktop.org/desktop-entry/latest/basic-format.html)/[§4 boolean](https://specifications.freedesktop.org/desktop-entry/latest/value-types.html)を確認。合成root名user/systemはDATA_HOME/単一DATA_DIRSの概念対応で、環境変数を設定して実Linux実装を試したものではありません。例/表/codeは独自制作、第三者本文/図転載なし。

未教材：実Linux menu/session、D-Bus/MIME、activation/install、NoDisplay/OnlyShowIn/NotShowIn/TryExec、localization、任意ID/入れ子・複数root・symlink、既存設定とのintegration、他browser/学習者評価。次案は別fixtureでNoDisplayとHiddenの違い、複数systemrootの順、localization選択、MIME/D-Bus activationを個別制作。全て未制作。Core/fullGate・commit/push・公開・install/設定/新権限・課金は対象外です。
