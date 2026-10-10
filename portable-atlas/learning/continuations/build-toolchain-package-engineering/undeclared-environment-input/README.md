# 実clangで追う、keyから抜けたCPATH header

[元のtiny build教材](../../../subjects/build-toolchain-package-engineering/README.md)のundeclared inputを実toolchainへ進めた継続単元。元教材は実ファイルからUTF8のtoy生成bytesを作った。今回は既存MacのApple clangを使い、Cをcompile/linkしてnative binaryを実行した。入口数や元教材の原票は変更しない。

前提はheader探索、SHA256、cache keyと出力digestの違い。`main.c` は `<banner.h>` をincludeし、`puts(BANNER)` を実行する。owned `headers/A/banner.h` は `#define BANNER "A"`、B側は `"B"`。stdlib headerを省くためputsの宣言をsourceに置くが、system linker/runtimeは依然として必要である。

## 予想→実行→比較→答え

source/compiler/flagsが同じなら、CPATHをA→Bへ変えても同じ成果物でよいだろうか。画面でbad-Bのstdoutを予想してから実行する。1操作は以下の5attemptで終了し、毎回owned temp/cacheを新しく作る。

| attempt | CPATH | keyに含めるinput | 事前期待hit/miss | 実binaryの期待stdout |
|---|---|---|---|---|
| bad-A | headers/A | source / compiler / flags | miss | A |
| good-A | headers/A | 上記＋実解決header bytes | miss | A |
| bad-B | headers/B | source / compiler / flags | hit | A（現在のBに不適合） |
| clean-B | headers/B | badと同じkey、cache bypass | miss | B |
| good-B | headers/B | 上記＋実解決header bytes | miss | B |

`oracle.json` は実行前の固定期待値。`check.py` はrunnerをimportせず、固定source/header/flagsからcanonical keyを再構成する。stdout/exit、CPATH、実compilerの `-MM -MT app main.c` 依存出力、key、実binaryのSHA256/sizeを照合する。bad-BがAを返す観測自体は予想どおりだが、現在header Bへ適合した成功ではない。

bad-Aとbad-Bのkeyは同一で、hitしたbinary bytes/digestも同一。clean-Bは同じB条件で再compileしてBを返すため、C sourceやcompilerが変わらなくてもheader探索結果は物理inputになると分かる。good-A/Bは同じlogical header名でもbytes hashが変わり別keyになる。good-BはmissでBを返す。

なお、別compileのA同士やB同士のnative binary digestは今回一致していない。同じstdoutはbyte同一の証明ではない。native metadataやlinkerによる差分原因はこの単元で切り分けていない。

## 実行と証拠

```sh
python3 -B check.py
python3 -B runner.py --inspect-evidence
python3 -B server.py
python3 -B runner.py --record
python3 -B skills/atlas-clang-cpath-input/route.py cpath-cache
```

このdirectoryを作業位置にする。checker/inspect/skillは保存証拠をread-onlyで見る。previewはdynamic `127.0.0.1` portを起動時に表示する。IABのbuttonは実compiler・binaryを実行し、旧原票を更新しない。終了はCtrl-C。原票保存は明示 `--record` のみで、新しいUTC directoryへ保存する。default runnerはowned一時実験を実行するが証拠を保存しない。

直接compilerを使った採用原票は `observations/20261005T103241829015Z/raw.json`。旧shim経由の成功rawも上書きせず保存している。UTC、Python/OS/architecture、invoked compiler `/Library/Developer/CommandLineTools/usr/bin/clang`、解決path、version、実compiler SHA256、input hex、最小env、全command argv/stdout/stderr/exit、key payload、成果物digestへ到達する。同directoryの5 `.bin` とsource/headerが保存成果物。toolchain identityは実行時に確認したApple clang 17.0.0、arm64-apple-darwin25.1.0。全systemenvは収集しない。

compiler子processのenvは明示 `PATH=/usr/bin:/bin`、`LC_ALL=C`、owned `TMPDIR`、relative `CPATH=headers/A|B` だけ。直接compilerには既存SDKを `-isysroot /Library/Developer/CommandLineTools/SDKs/MacOSX.sdk` で明示する（読取確認時MacOSX26.2.sdkへのsymlink）。SDK bytes全体はkeyへ含めていない。binaryはPATH/LC_ALLだけ。子processのworking directoryもowned tempで、compiler temp prefixは原票内で `$WORK` へ正規化する。ユーザーのCPATHやSDKROOTを変更しない。compilerが実際に依存と報告したheader pathのbytesを読み、good keyへ入れる。

初回は `copyfile` がcache復元binaryの実行bitを落とし、bad-BのexecがPermissionError errno 13になった。`observations/20261005T102516681226Z` の不採用directoryに生成済み2binary、修正前runner、failure.jsonを保持。`copy2` でowned成果物のmodeを保持して全attemptを再実行した。採用原票だけを成功として数える。通常sandboxのpreview bind拒否も `sandbox-preview-failure.txt` に保存し、許可済みホストreviewで所属previewを実行する。

## 原典と実務判断

[Clang ENVIRONMENT / CPATH](https://clang.llvm.org/docs/CommandGuide/clang.html#environment) はCPATHが非system header探索pathを追加すると説明する。[Clang Dependency file generation / -MM・-MT](https://clang.llvm.org/docs/ClangCommandLineReference.html#dependency-file-generation) はuser header依存の取得に対応する。compiler flag一覧とsource hashだけで入力が尽くされたとは判断しない。keyに何を入れたかと、compilerが何を読んだかを照合する。

修正版が扱うのは、この1つのbanner.hのbytesだけ。[build環境の境界](https://reproducible-builds.org/docs/perimeter/)を広げて考える必要があり、実driver binary hashはSDK、linker、system library、compiler resource files全体のidentityではない。CPATHをkeyへ文字列として入れるだけでも同じpathのheader内容変更を見逃せる。今回のgood keyは解決bytesを含める。

cache hitは速さ、全hermeticity、cross-host/OS再現性、ABI互換、supply chain真正性の保証ではない。速度計測、署名、publish、remote cache、外部package/SDK更新は未実施。Apple toolchainがlink時に生成する通常metadataと、ユーザーによるrelease署名操作を混同しない。

## 未教材と次の有限実験案（未実行）

| 問い | 具体入力・操作 | 比較観測 | 公式locator |
|---|---|---|---|
| 同じCPATH文字列のまま内容変更 | owned headers/A/banner.hをA→Cへ変更しCPATH=headers/Aは固定。path-only keyとbytes keyを比較 | path keyのhit/A対clean C、bytes keyのmiss/C。現在解決bytesとartifactの適合を分ける | [Clang ENVIRONMENT / CPATH](https://clang.llvm.org/docs/CommandGuide/clang.html#environment) |
| 探索順・shadowing | owned A:BとB:AのCPATHを比較。同じheader名でA/Bを配置。空entryは別試行のowned cwd headerだけで検証 | `-MM` が報告する解決path、stdout、key。path候補一覧と実採用依存の違い | 同原典CPATHの探索順・empty entry、[Clang -MM](https://clang.llvm.org/docs/ClangCommandLineReference.html#dependency-file-generation) |
| native bytes差とlinker境界 | 同一inputを同じ出力名・別出力名・別owned cwdでclean compile。SDK/linkerは更新せず実path/versionを最小記録 | stdout同一とbinary digest差、native metadata差を比較し、差の原因を判定する | [Clang DESCRIPTION / Linker](https://clang.llvm.org/docs/CommandGuide/clang.html#description)、[build環境](https://reproducible-builds.org/docs/perimeter/) |

未網羅はSDK/sysroot、linker/library/resource files、他環境変数、transitive/system header、generated header、時刻/path/order、別OS/ABI、remote cache認証・破損・同時write。次案は追加実行済みとして計上しない。有限単元のchecker/Skill/IAB/capture/cleanup/hash bindingは `observations/verification.json` と `observations/qa.json`。全Atlas/Subject完了、Core/fullGate、commit/pushは主張しない。

identity修正では/usr/bin/clangの入口hashとCommandLineTools実compiler hashを区別した。直接実行の初回はSystem library未検出でlink exit=1になり、failure.jsonと修正前sourceを保持した。既存SDK sysrootを明示して再実行し、SDK更新・環境全収集はしていない。旧shim rawのsource bindingはそのdirectoryのrunner-at-execution.pyへ照合する。
