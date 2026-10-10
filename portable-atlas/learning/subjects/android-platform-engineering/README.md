# Androidを学ぶ入口 — 消えたActivityのcounterはどこへ？

有限1教材。Python標準libraryのstate simulatorでrotationとsaved-instance-state restoreを実行する。Android SDK/実device/emulatorは未実行。単一Activity-like modelの検証であり、全Subject完成ではない。

**前提 → 主要概念/仕組み:** objectの寿命、state machine、小さなserializationを理解して進む。Activity instanceの破棄とprocess deathは別。counterをmemberに置くだけでは再生成時に失う。明示saveした小さなsnapshotが新instanceへ渡された場合、version/typeを検査して復元できる。[有限契約](SPEC.md)はcallback順/codec/全仮定を説明する。

**今回の実装・正常/境界/意図異常:** [UI](index.html)は保存原票をstep再生し、正常serializedと意図異常ephemeralを、[独立transition/save oracle](oracle.py)・[手記](handtrace.json)と比較する。中心caseはcreate→start→resume→tap×3→pause→stop→save→destroy_rotate→create→start→resume。正常counter3、保存漏れ版0、新instance2/同process1。process deathにはonDestroyを挿入せず、snapshotがあれば新processで復元、なければ0。古いsnapshot/利用不能/finish/同instance restart/0..9境界/不正saved state/無効transitionも比較する。

**予想 → 操作 → 比較 → 原典/実装 → 答え:** UIで「counter3をrotationしたらいくつ？」を予想。case選択と次event/全event/reset、counter・instance/process・saved token・lifecycle図を比較。原典と実装を開いて答えへ。UIはPythonの保存実行をreplayし、Androidのcallbackを発火させない。

このdirectoryで実行:

```sh
python3 -B runner.py
python3 -B runner.py --input-json '{"saved":null,"events":["create","start","resume","tap"]}'
python3 -B checker.py
python3 -B route.py lifecycle
python3 -B route.py sdk-install
python3 -B preview.py
```

runner acceptedはexit0、input/runtime rejectionはexit2。events1..32、counter0..9、saved nullか小さな独自JSON、余分key/未知event/外部path拒否。input拒否はtraceなし、runtime拒否は直前までのtraceを保持。通常runner/checker/route/observeはread-only。原票更新は `python3 -B observe.py --write-evidence`、artifact binding更新だけは `python3 -B checker.py --seal-evidence` を明示して行う。通常検査が失敗した時、勝手に原票を書き直さない。

[保存raw](evidence/raw.json)、[UTC/環境/input/source/artifact digest](evidence/run.json)、[実IAB QA/cleanup](evidence/ui-qa.json)、[integrity](evidence/integrity.json)、[検証結果](evidence/verification.json)。[counter図](evidence/counter-trace.svg)は生成図、IAB JPEGは実capture。previewはdynamic127.0.0.1だけ、確認後Ctrl-Cで終了。教材内[skill](skills/atlas-android-platform-engineering/SKILL.md)は既存runner/checker/UI/原典への限定route、global installなし。

**実務判断:** 軽いUI stateは明示snapshotにして検査し、最新saveのタイミングとdata ownerを確認する。snapshotはdurable DBではない。process deathでonDestroyに保存を任せない。finish後の別launchを復元扱いしない。[公式contract](SOURCES.md)を読み、API/version/実環境で確認する。

**限界 → 次の学習 → 原典:** explicitsaveを入力した時だけsnapshot成功と仮定。process deathでsnapshotが必ず提供される/最新/永続とは保証しない。MAX32/counter9/JSON128byteは作者の有限化でAndroid制限ではない。全Androidcallback順、実Bundle/SDK/device/emulator/OS killは未実証。[COVERAGE](COVERAGE.md)に主要未教材概念の問いと次1: owner/ViewModel、次2: durable/async、次3: IPC/platform、次4: 実環境testの4実験と公式locatorを整理した。[SOURCES](SOURCES.md)で取得確認済みとlocatorのみを区別する。
