# OCIとcontainer engineeringを学ぶ道筋

この文書は[OCI objectとlayer mapの既存教材](README.md)から、圧縮、削除、platform、metadataとruntimeの境界へ進むための補足です。有限教材の補足であり、分野全体の学習完了を示すものではありません。以下の次実験はすべて未実行です。

## 1. 前提と主要概念

byte列、SHA-256、JSON、descriptor、tar member、相対pathを理解します。imageの内容、ホストCPU/OS、containerが実行するprocessを分けます。digestは内容一致の検査材料で、誰が作ったかの信頼を単独で証明しません。

学ぶ順序は **layout/index → descriptorとblob → manifest/config → layer changeset → platform選択 → runtime bundleとprocess → 隔離・資源・配布・信頼** です。

- manifestのlayer順序はbaseから上位です。同名fileは上位で置換され、whiteoutは下位の対象を隠します。
- descriptor digestは参照blobのbyte列、DiffIDは非圧縮tarのbyte列を対象にします。非圧縮の既存例で同じでも、圧縮全般には拡張しません。
- layerの適用後map、ホストへの展開、overlayfs mount、container起動は別の観測です。
- specで有効なentryをsubset readerが拒否することがあります。未対応拒否を全OCIで無効と呼びません。

## 2. 予想から既存実測へ

[UI](index.html)で2層を重ねた最終pathを予想し、[reader](oci_subset.py)、[成功原票](observations/20261005T052300160763Z-oci-layer/observation.json)、[command](observations/20261005T052300160763Z-oci-layer/command.json)、[artifact一覧](observations/20261005T052300160763Z-oci-layer/artifact-index.json)、[QA](qa/QA.md)を読みます。この文書作成ではtar生成・reader・checkerを実行していません。

| 条件 | 保存済み結果 | 読み取れること |
|---|---|---|
| 正常2層 | messageはversion two、new追加、stable保持、obsolete削除 | 上書きと明示whiteout |
| 同層file後にwhiteout | 同層追加fileを保持 | whiteoutが消すのは下位の対象 |
| 下位に対象なし | no-op、marker非表示 | 削除対象なしを通常fileにしない |
| traversal / absolute path / 重複path | path規約で拒否 | subsetの入力境界 |
| symlink / opaque whiteout | 未対応拒否 | OCI全体の無効性ではない |
| metadata・blob改ざん | descriptor-mismatch、未適用 | 内容参照の整合性 |
| descriptor自己整合、DiffID不一致 | diff-id-mismatch、未適用 | configの非圧縮内容bindingも検査 |

保存された11結果は、実生成したlayout/tarを読み、memoryのpath→bytes mapへ適用したものです。正常最終mapは3fileで、内容末尾の改行も原票にあります。ホストextractはしていません。同入力のrepeat-layoutはbyte一致ですが、任意builderの再現性を保証しません。

初回runのdirectory初期化不足によるexit1、初回checkerの原票不足によるerrorは、意図した拒否caseと別の失敗記録です。独立checkerはproducer/consumerをimportしませんが、hashとtar parserは同じstdlibです。configのlinux/amd64はimage metadataで、実観測hostのDarwin/arm64でcontainerを実行した意味ではありません。

## 3. 実務で何を判断するか

imageを読むときは、参照chainのdigest/size、layer順序、DiffID、media typeとplatformを分けて検査します。展開するならpath、links、metadata、容量の境界が別途必要です。hash一致と、署名・発行者・脆弱性・実行時権限の判断を分けます。

containerを使う判断には、runtime-spec、rootfs、process、mount、namespaces/cgroups、capabilities/seccomp等の実検証が必要です。この教材のmapから隔離やrootless、安全なimage、実起動を推論しません。仕様のSubsetを使う場合は、有効だが未対応の入力を説明できる拒否にします。

## 4. 一次資料への道筋

| 原典とlocator | 読む目的 |
|---|---|
| [OCI Image Spec v1.1.1 Layer](https://github.com/opencontainers/image-spec/blob/v1.1.1/layer.md)、Distributable Format / Whiteouts / Opaque Whiteout | tar changeset、圧縮、下位削除と同層保持 |
| [v1.1.1 Config](https://github.com/opencontainers/image-spec/blob/v1.1.1/config.md)、Layer DiffID / rootfs | 非圧縮tarのidentityと順序 |
| [v1.1.1 Descriptor](https://github.com/opencontainers/image-spec/blob/v1.1.1/descriptor.md)、Digests / size | blob内容と参照metadata |
| [v1.1.1 Image Index](https://github.com/opencontainers/image-spec/blob/v1.1.1/image-index.md)、manifests / platform / Platform Variants | OS・architecture・variantと候補選択 |
| [OCI Runtime Spec v1.2.1 Runtime](https://github.com/opencontainers/runtime-spec/blob/v1.2.1/runtime.md)、Lifecycle | imageの読解とcontainer lifecycleの間にある別の契約 |

既存layout/manifest資料のlocatorは[sources.json](sources.json)にあります。`oci-layout`内の1.0.0はlayout markerで、参照Image Spec v1.1.1とは別の版識別です。

## 5. 未教材の問いと次実験

| 未教材 | 問い | 次の入口 |
|---|---|---|
| gzip/zstdとDiffID | 圧縮byteと非圧縮byteのidentityはどう違うか | 実験1はgzipのみ |
| opaque whiteout | directory下の下位entryと同層追加をどう扱うか | 実験2 |
| multiarch/index nesting | 複数候補から何を選ぶか | 実験3は浅いindexのみ |
| mode/owner等のmetadata | 同じfile内容でもlayer identityは同じか | 実験4 |
| links、devices、xattrs、host展開、overlayfs | 実filesystemの意味と安全な展開は何か | 別の仕様読解・実環境が必要 |
| runtime、隔離、資源制御、rootless | 実processとホストの境界を何で強制するか | Runtime Specから別の実起動検証へ |
| registry、署名、SBOM/CVE、運用性能 | 内容取得、発行者の信頼、安全性をどう検証するか | このunsigned layoutでは未評価 |

## 6. 次の実験案（4本、すべて未実行）

1. **gzip blob digestとDiffIDを分ける。** 実験専用fixtureで同じ非圧縮tarをgzip化し、gzip headerの時刻等が異なる2blobを作ります。予想は展開tarがbyte一致でも圧縮blob digestは異なり得て、DiffIDは同じになることです。圧縮・非圧縮それぞれのbyte数/hash、manifest descriptor、config DiffID、解凍結果を独立表へ照合します。改ざん・展開上限・DiffID不一致を別条件にし、圧縮サイズだけで資源上限を決めません。原典はLayer Distributable FormatとConfig Layer DiffIDです。zstd、registry転送、container起動は行わない案です。

2. **opaque whiteoutを仮想mapで実装する。** 独立fixtureの下位にdirectory直下と孫pathを置き、上位にopaque markerと新fileを置きます。予想はそのdirectoryの下位子孫が消え、同層追加はmarker配置順にかかわらず残ることです。上位member順の有限permutationを手書き最終mapと照合し、隣の似たprefixを消す故障版も比較します。原典はLayer Opaque Whiteoutです。既存readerの未対応拒否を変更済みとは扱わず、host展開や全filesystem型の適合は残します。

3. **浅いimage indexでplatform候補を選ぶ。** 合成のlinux/amd64とlinux/arm64のmanifest descriptorを持つ独立indexを用意します。requestのOS/architecture/variantを明示し、候補なし・複数一致・platform欠損を別表にします。予想はhost metadataを無条件採用せず、明示requestで選択結果が変わることです。独自Subsetの欠損時拒否契約と、原典のoptional属性・複数一致時の推奨順序を分け、選んだdescriptorのdigest/sizeも照合します。原典はImage Indexです。選択の成功を実CPUでの実行可能性やnested index全対応と読みません。

4. **内容とtar metadataのidentityを比較する。** 同じpath・本文でmodeだけを変えた2tarを、他のheader値とmember順を固定して生成する案です。予想は本文hashが同じでもtar byte列とDiffIDが変わることです。tar header、member本文、mode、tar hash、内容だけのmapを別々に保存し、手書きmetadata表と照合します。原典はLayerのDistributable FormatとConfig Layer DiffIDです。本文mapが一致してもfilesystem全体が同じとしません。ホストchmod/chown、実uid mapping、xattrs、実mountは対象外です。

## 7. 資料の取得・検証状況

2026-10-05に上記5つのOCI公式GitHub本文を、Image Spec v1.1.1 / Runtime Spec v1.2.1のtagで取得して確認しました。今回取得不能だったURLはありません。既存layout/manifest資料はsources.jsonのbindingを読み、今回本文を再取得した5資料と区別しています。第三者本文・図・code exampleは保存していません。

追加したのはこの文書だけです。tar生成、reader、checker、Docker、container、registry、server、UI、global gateは実行せず、既存原票・QA・digestを更新していません。次実験の予想は新たな実測証拠ではありません。
