# Build / toolchain / package engineering — cache hitは正しい成果物か

標準ライブラリで実ファイルから生成bytesを作る閉じたtiny build教材。13ケース・21回を実行し、入力依存/action/toolchain/builderのkey、local action cache/CAS、生成object/bundle bytesを独立oracleで照合する。production toolchainの再現性や製品互換性を保証せず、科目全体の完成ではない。

前提はファイルbytes、内容hash、mtime、DAG、依存、hit/miss。[index.html](index.html) でdecision・hit数・現在入力に正しいbytesかを予測し、case/attempt/actionを操作して比較する。「input依存 → action key → hit/miss → 実生成bytes → 手計算との比較 → raw/原典 → 答え」の学習経路。UIは保存済み観測readerであり実行は `--record` 時だけ。

前単位application-configuration-feature-managementは設定layerとactor rolloutを扱った。本教材はtoolchain labelがbuild keyと出力bytesへどう影響するかを扱い、mtimeというmetadataと内容identityを区別する。

通常DAGは source.txt + suffix.txt → object.bin、header.txt + object.bin → bundle.bin。compileは `object:toy-1\n` + sourceの大文字bytes + suffix、packageはheader + objectを実ファイルへ書く。source=hello、suffix=!改行、header=bundle改行なのでobjectは `object:toy-1\nHELLO!\n`、bundleは `bundle\nobject:toy-1\nHELLO!\n`。toy-2ではmarkerがtoy-2に変わる。これらbinはUTF8のtoy製品で、native compiler、wheel、実行可能形式は実装していない。

content keyはcanonical JSONのmode/action/宣言依存順/toolchain/builder digestと各依存bytesのSHA256をhashする。action cacheはkey→output digest/size/payload、CASはoutput digest→実blob。output digestとaction keyは用途が違う。cache hitでもblob digest/sizeを照合する。実cacheの破損fixtureは未実行で次の実験。

同じ入力2回目は2 hit。sourceをhello→worldへ同じmtimeで書き換えるとcontent版はobjectとbundleが2 missになりWORLDを生成する。mtime-onlyの意図的bad keyは依存mtimeだけを見るため2 hitで古いHELLOを返す。oracleはこの悪い観測も期待どおりと照合し、別にfresh-match=falseと表示する。hitという状態だけでは正しさは決まらない。

suffix !→?の変更とtoolchain toy-1→toy-2は2 missで別bytes。sourceをtouchだけするとcontent版は2 hitで同じbytes、mtime-only版は2 missでも同じbytes。同一入力を別work/cacheでclean rebuildすると2 missかつbyte同一。空sourceも正常生成。missing dependency/cycle/unsupported actionはaction実行前に拒否し成果物を作らない。

mtimeはrunnerが作る専用fixtureのinputs/outputsだけをos.utimeで制御する。基準1700000000000000000ns、touch時は+10秒。output mtimeは依存の最大mtimeへ揃えるtoy規則。既存sourceや他担当fileはtouchしない。内容を変えたのにmtimeが同じ、という意図的比較を再現するための設定で、現実build systemのtimestamp規則を模倣する保証ではない。

実務で判断できるのは、keyに依存とtoolchainが入っているか、hitした生成bytesが現在入力に適合するか、mtime変更だけの不要buildと内容変更の見逃しを区別すること。same-host clean rebuildの同一性は他host/OS/compilerへの再現性証明ではない。toolchain labelとbuilder source digestはここでの有効範囲でありcompiler binary/ABI/supply chainの真正性を認定しない。

```sh
python3 runner.py                     # defaultは既存証拠のread-only確認
python3 checker.py
python3 test_negative.py              # owned一時コピーの改竄5種 + read-only確認
python3 runner.py --record            # 明示した原票更新だけ
python3 preview.py                    # 一時dynamic loopback、終了時Ctrl-C
python3 skills/atlas-build-toolchain-package-engineering/route.py tiny-build
```

[current.json](current.json) からUTC時刻、Python/OS、fixtures、物理input hex/digest/mtime、raw stdin/stdout/stderr/exit、実生成bin、action key payload、cache metadata/CAS blob、独立oracle、source/artifact digestへ到達する。[checker.py](checker.py) はbuilder/runnerをimportせず、固定入力/生成bytes/hit-missを用いてkeyを独立に組み立てSHA256で検算する。[qa.json](qa.json)・[verification.json](verification.json)・[ui-observations.json](ui-observations.json) に実IAB QAを保存。

主要な未カバー領域はhermeticity/undeclared input、real package/ABI/platform、dependency resolution/lock、cross-host reproducibility、remote cache trust/concurrency、parallel scheduling/recovery、署名/provenance/publish。[coverage.json](coverage.json) に問い・次の4実験・公式locatorを対応させる。外部package install、Bazel/GNU Make/production compiler、registry公開、Git操作、remote serviceは実行していない。

一次資料: [Bazel remote caching](https://bazel.build/remote/caching) のaction cache/CAS、[Python os stat/utime](https://docs.python.org/3/library/os.html#os.stat_result.st_mtime_ns)、[graphlib](https://docs.python.org/3/library/graphlib.html)、[Python package formats](https://packaging.python.org/en/latest/discussions/package-formats/)、[Reproducibility Quickstart](https://reproducible-builds.org/docs/getting-started/)。[sources.json](sources.json) に確認日/locator/取得範囲を保存し、未実行toolと区別する。
