# OCI objectと2層の仮想path map

問い: 同名fileと削除印を持つ上位layerを重ねると、何が残るか。

Python標準ライブラリで合成OCI image layout・index・manifest・config・非圧縮tar blobsを実生成し、実fileのdigest/size、config DiffID、tar memberを読んだ。通常fileの内容はmemoryのpath→bytes mapへ適用し、ホストへextractしていない。上位の同名fileは上書きされ、明示whiteoutで下位の対象は消え、削除印そのものは残らなかった。同じlayerに追加したfileはwhiteoutの配置順にかかわらず保持した。

これはOCI filesystem changesetの小さなsubset教材。container起動、隔離、実mount、runnable imageや全OCI適合の証明ではない。

## 開く・検算・新しい原票を作る

このdirectoryでloopback HTTP serverを起動する。空きportを確認するか、port 0で動的割当にする。他taskのlistenerを止めない。

```sh
python3 -u -m http.server 0 --bind 127.0.0.1
```

出力にあるportの `http://127.0.0.1:PORT/` を開き、titleとField ID `oci-container-engineering` が一致することを確認。終了はそのserverのCtrl-C。

画面は予想→object検査→tar生成入力→実読取map比較→原典/実装→答え。画面操作では新生成・file変更をしない。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 checker.py
node --check app.js
```

通常checkerはread-onlyで、新規原票やcacheを作らない。新しい合成実生成を明示して依頼した場合だけ次を実行する。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 runner.py --record
```

`runner.py` はoptionなしでは変更せずexit 1。`--record` は20秒上限で実験を実行し、新しいrun directoryへ保存、成功時だけ `observation-data.js` をatomic replaceする。失敗commandと途中fileを保持し、直前の成功表示を消さない。stderrの絶対module/runtime pathはprivacyのため置換し、error・exit・line番号・時刻は保持する。依存install、socket、Docker、registryは不要。

## 今回の実観測

成功run `20261005T052300160763Z-oci-layer`、UTC `2026-10-05T05:23:00.221549Z` — `2026-10-05T05:23:00.278582Z`。実行hostはCPython 3.9.6 / Darwin 25.1.0 / arm64、attempt 1 / retry 0。合成imageのconfigはlinux/amd64であり、host/runtimeの実行identityとは違う。

[command.json](observations/20261005T052300160763Z-oci-layer/command.json) にcommand、stdout/stderr、exit 0。[observation.json](observations/20261005T052300160763Z-oci-layer/observation.json) に11結果、input、trace、時刻、producer Source bindings。[artifact-index.json](observations/20261005T052300160763Z-oci-layer/artifact-index.json) に全96 fileのSHA-256/size。各caseにinput/resultとOCI layoutの実fileがある。同入力で作った [repeat-layout](observations/20261005T052300160763Z-oci-layer/repeat-layout/) は正常layoutの全fileとbyte一致した。

| 条件 | object / DiffID | Layer map | 実拒否理由 |
| --- | --- | --- | --- |
| 正常2層 | 一致 | 適用 | なし |
| 同層fileの後にwhiteout | 一致 | 同層fileを保持 | なし |
| 下位に削除対象なし | 一致 | no-op、印非表示 | なし |
| `../escape.txt` | 一致 | 拒否 | `noncanonical-path` |
| `/escape.txt` | 一致 | 拒否 | `absolute-path` |
| symlink | 一致 | 未対応拒否 | `unsupported-entry-type` |
| opaque whiteout | 一致 | 未対応拒否 | `unsupported-opaque-whiteout` |
| 同一tarのpath重複 | 一致 | 拒否 | `duplicate-path` |
| manifest metadata改ざん | 拒否 | 未適用 | `descriptor-mismatch` |
| tar内容の同長改ざん | 拒否 | 未適用 | `descriptor-mismatch` |
| 自己整合metadata、DiffIDだけ不一致 | 拒否 | 未適用 | `diff-id-mismatch` |

正常の最終mapは `app/message.txt = version two`、`app/new.txt = added`、`etc/stable.txt = unchanged`。`app/obsolete.txt` とwhiteout markerはない。tarの生成入力表示と、実tar読取・検査後のmapは画面で分離した。拒否時のpartial snapshotは成功のfinal mapへ流用しない。

初回runは観測directoryの親未作成でexit 1だった。[失敗command](observations/20261005T052156301705Z-oci-layer/command.json) を保持し、親directory初期化を修正して上記の別runで実測した。初回checkerは原票未生成で0 tests/errors=1、修正後checkerの6 testsはpass。この失敗を11個の意図した拒否caseと混同しない。

## 実装・独立oracle・subset

[oci_subset.py](oci_subset.py) はdescriptorを辿りSHA-256とsizeを比較。configの順序付きDiffIDは実非圧縮tarのdigestと比較する。tarfileでmemberのbytesをmemoryへ読み、canonical relative path・重複・型・whiteoutを全検査してから新しいmapを返す。whiteout処理と同層file適用を分け、入力lower mapは変更しない。

[checker.py](checker.py) はproducer/consumerをimportせず、保存fileから別code pathでobject hash・tar member・mapを再計算する。hash primitiveとtar parserは同じstdlibであり、別暗号実装や別tar実装のcross-validationではない。6 testsで全11結果、全index、raw stdout、Source binding、同入力bytes、lower-only whiteout、追加path拒否と入力map保持を確認。metadata chainとtar blobsは署名されておらず、digest一致をauthenticityとしない。

今回のsubsetは1manifest・linux/amd64 config・2層・非圧縮USTAR・canonical ASCII相対path・通常file・明示empty whiteout。1blob 2MiB、1member 64KiB、128entries。UTF-8 file内容を表示する。`./`、directory metadata、links等は全OCIでは可能でも本readerでは扱わない。

## 一次資料・未教材Coverage

正本参照はOCI Image Spec v1.1.1の [Image Layout](https://github.com/opencontainers/image-spec/blob/v1.1.1/image-layout.md)、[Manifest](https://github.com/opencontainers/image-spec/blob/v1.1.1/manifest.md#image-manifest)、[Config DiffID](https://github.com/opencontainers/image-spec/blob/v1.1.1/config.md#layer-diffid)、[Layer Whiteouts](https://github.com/opencontainers/image-spec/blob/v1.1.1/layer.md#whiteouts)、[Descriptor Digests](https://github.com/opencontainers/image-spec/blob/v1.1.1/descriptor.md#digests)。[sources.json](sources.json) はURL/locator/教材bindingだけを保持し、第三者本文を保存しない。`oci-layout` markerの `1.0.0` はlayoutの版で、参照spec v1.1.1と矛盾しない。

opaque whiteoutはOCIで有効だが今回は未対応拒否。非圧縮tarのdescriptor digestとDiffIDは同じだが、圧縮layer全般へ一般化しない。全仕様conformance toolの代替ではない。

実container、runtime-spec、namespaces/cgroups、隔離、capabilities/seccomp/rootless、overlayfs、ホスト展開、file権限/所有者/xattrs、directory metadata、hardlinks/devices/FIFO、opaque実装、gzip/zstd、multiarch/index nesting、registry/distribution、署名/SBOM/CVE、image安全性、production性能は未教材・未実行。全Subject・理解度完成は未測定。

再利用入口は [module-local Skill](skills/atlas-oci-container-engineering/SKILL.md)。global installなし。実画面QAとowned cleanupは [qa/QA.md](qa/QA.md)。commit/push/公開はこの有限教材の作業対象外。
