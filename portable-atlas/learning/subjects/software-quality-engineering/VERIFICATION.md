# テスト品質教材の実観測

問い：行coverageが高いだけでは区別できない境界誤りを、追加testで検出できるか。

2026-10-05 13:44:38 JST、Mac darwin arm64、Node v25.2.1、実装 `quality-interval-lesson/1`。`node verify.mjs observations/node-20261005-attempt-01` を実行し成功した。生の入力／期待値／実値／kill・survive／表示関数sourceは [runtime.json](observations/node-20261005-attempt-01/runtime.json) に保存した。

## coverageと実mutation matrix

別processで実行したコマンド：

```sh
node --test --experimental-test-coverage --test-coverage-include=**/core.js --test-reporter=spec coverage.test.cjs
```

[生stdout](observations/node-20261005-attempt-01/coverage.stdout.txt)、[stderr](observations/node-20261005-attempt-01/coverage.stderr.txt)を保存。exit 0、1 test（3 assertion）成功、skip／todo 0。Node/V8のcore.js行／branch／function coverageはいずれも100%。対象は元関数のファイルだけで、変異のcoverageを測った数字ではない。

| 実装 | 弱い3入力 | 境界＋有限集合258入力 | 最初に区別する入力 |
| --- | --- | --- | --- |
| 元関数 | passed | passed | 仕様oracleと一致 |
| M1 下端を含めない | survived | killed | x=2, [2,5) |
| M2 上端を含める | survived | killed | x=5, [2,5) |
| M3 AND→OR | killed | killed | x=1, [2,5) |
| M4 空区間を受理 | survived | killed | x=2, [2,2) |
| E1 比較の否定形 | survived | survived | 同値領域では区別されない |

非同値4件の集計は1/4→4/4。E1込みの生集計は1/5→4/5。E1を削除して分母を隠さず、整数-10〜10・lo≤hiの領域で比較の否定が同じ真理値を返す理由を明示する。NaNや任意の比較契約には一般化しない。

強いsetは弱い3＋境界3＋有限集合252入力。独立仕様oracleは整数区間を列挙して所属を調べ、対象関数の二つの比較式をコピーしない。252件はlo／hiを-3〜3、lo≤hi、xを-4〜4にした全組合せ。無限入力領域の証明や乱択property testではない。

## 実画面QA

13:45:59〜13:46:01 JST、Codex背景IABと教材専用localhost。共有Chrome／global viewportを変更していない。Browser versionはこの経路では採取していない。

7状態を実操作：弱いset、下端追加、上端追加、空区間追加、有限集合追加、弱いsetへ戻す、強いsetボタン。検出数1→2→3→4、入力数3→4→5→6→258を確認した。Browserの実JSONを同じJSのNode実行結果と照合し、全matrix・表示statusが一致した。

追加8確認は6実装のsource切替、Tabで下端checkboxへ移動、答え合わせ展開。表示codeは実行関数のtoStringと一致した。Node原票のcore.js／experiment.js digestをBrowserで再計算して照合し、100%の表示が確認できた。warn／error記録0。

[Browser生記録](observations/browser-20261005-attempt-01/browser.json)と[実画面](observations/browser-20261005-attempt-01/matrix.jpg)を保存。画像は1280×720 JPEG、75,768 bytes、後加工・合成なし。実際に開いて左右の検出差分と失敗入力を確認した。viewportの一部分で、E1を含む全行は画像内に収まらないため、生記録でも照合する。

画面のcheckbox操作は実JS再実行、図と状態表示はその結果の説明モデル。NodeのcoverageはBrowserで再測定せず、保存原票を照合して表示する。パケット監査、実行Trace、file URL、狭幅端末、支援技術、多Browser、学習者の理解度は未確認。

## Skillと保存範囲

[Skill](skills/atlas-software-quality-engineering/SKILL.md)は既存UI／コード／runner／原票への短い入口。quick_validate.pyを実行し、`Skill is valid!`。全相対リンクも照合した。

同じ担当の軽い確認：上端test追加の依頼を既存run(['upper'])へ渡し、M2 killed／元関数passedを観測。CI全体の品質保証の依頼にはscopeを読み、この教材では未対応、固定scoreで保証しないという判断を確認した。[control記録](observations/skill-control.json)を参照。独立Agent Evalや全Subject Skill完成、global installの証拠ではない。

Source digestはNode原票と現在の6ファイルで一致。実観測のないmetadataを補っていない。

- core.js：`93b0777f46e936855ce16d8e268053d3a3702fc758ddc1ec59b163b223866cad`
- experiment.js：`3d556a428ccdc23ec0dce6d5f8b141c4b91b4a6099076cbf04469f04449e0145`
- index.html：`156d099acf9615cc5ea8fe06dce53c48599c768088871a1072da72d7e3474f05`
- runtime.json：`b8126153d21296645b9c622005bc135eef9f33f65eb48574651f19f1167e4778`
- browser.json：`fe83b133c85b3e4861e43355226a6d62411401ec7cebd85e97091a77284630bf`
- matrix.jpg：`f59bd5d668106a9cacd40fb2af5a7e939cfa4cc1ce69e7b8ce769a5a21d6c97d`

未教材領域はscope.jsonと画面の表に残す。旧教材やPortal共通文書、Core／Graphを編集せず、このmodule内に追加。公開・commit・push・installなし。背景タブとtask-owned serverを終了し、全Subject完成や品質保証へ読み替えない。
