# 二分探索教材の実観測

問い：half-openの反復範囲と下限位置の不変条件を保ち、境界更新の誤りと停止性を説明できるか。

結論：Nodeの825入力ケースで下限位置・先頭一致が独立の線形走査による期待値と一致した。背景IABの7プリセット・5追加確認でJSの出力と図の段階表示を照合した。学習者の理解度を測定した結果ではない。

## 実装を実行した記録

環境はMac darwin arm64、Node v25.2.1、実装version `binary-range-lesson/1`。2026-10-05 13:31:44 JSTに最終Sourceで次を実行した。

```sh
node verify.mjs observations/node-20261005-attempt-03
```

生の観測JSONは [runtime.json](observations/node-20261005-attempt-03/runtime.json)。標準出力も同じJSONを出す。入力は長さ0〜8・値0〜2の整列列、目標-1〜3。独立oracleはfindIndex／indexOfによる線形走査。さらに7例の状態列と、不正数値・小数・33件・範囲外の4入力拒否を確認した。Python bisectを実行した証拠ではない。

| 入力 | 正常 | 意図的な異常／比較 |
| --- | --- | --- |
| 1,3,5 / 3 | 挿入位置1・一致index1 | hi = mid - 1で不変条件が破れ、一致なしと誤答 |
| 1,3 / 4 | 挿入位置2・一致なし | lo = midで[1,2)を維持。条件成立のまま非進捗で診断停止 |
| 1,3,3,3,5 / 3 | 最初のindex1 | 重複の先頭境界を確認 |
| [] / 3 | 挿入位置0・0反復 | 空列にアクセスしない |
| 3,1,2 / 3 | 未整列を拒否 | 強行版は見落とし、線形はindex0 |
| 0,2,…,30 / 31 | 探索4比較・一致確認0 | 線形16比較、前提確認15比較は別 |
| 0,2,…,30 / 0 | 探索5比較・一致確認1 | 線形1比較。二分探索が常に少ないわけではない |

不変条件の診断走査・配列コピー・前提確認・図描画を加えた実行全体はO(log n)の探索本体と同じではない。表示比較数は値に対する比較だけで、性能ベンチマークではない。

## 実画面とBrowserの説明モデル

共有Mac Chromeの代わりにCodex背景IABと、教材専用の127.0.0.1プレビューを使った。Browser製品versionは採取していない。global viewport変更なし、実表示は1280×720。7入力の初期・一段目・終端を操作し、画面から読み取った実行JSONがNodeの同じ例と一致した。候補の色・index・範囲と実行記録も一致した。

追加確認は最終説明と候補消失の段階、空要素入力の拒否、巻戻し、Tabで配列入力へ移動、答え合わせ展開。Browserのwarn／error記録は0。空要素拒否時は前の有効な観測を残し、その状態を画面で明記する。

生記録：[browser.json](observations/browser-20261005-attempt-01/browser.json)。一段再生は実行済みJS状態列の説明モデルで、Nodeの実行順を追うデバッガやOS実行時間の再現ではない。Browserの隠れた状態を結果とせず、表示JSON・範囲・セルを観測した。

画像は実表示のviewport撮影で、後加工・合成なし。3枚を実際に開いて比較枠・条件・境界を確認した。全ページや全入力の画像ではない。

Browser観測時刻は13:30:20〜13:33:28 JST。

| 画像 | bytes | 実寸 | SHA-256 |
| --- | ---: | --- | --- |
| [lost-final.jpg](observations/browser-20261005-attempt-01/lost-final.jpg) | 77251 | 1280×720 | a1947d2622bc6c83164f0442c0ca47414693cfae1c09ca5237944c2496238a0e |
| [lost.jpg](observations/browser-20261005-attempt-01/lost.jpg) | 77176 | 1280×720 | 714fa37bd3ec26a4082f5cb3560ec2b8b08bb6febf154b0e3775e29a085a3c7e |
| [stalled.jpg](observations/browser-20261005-attempt-01/stalled.jpg) | 77091 | 1280×720 | bc672ff8ab79b03189271eb6e070ab0b8cd99ab93399153683572423d5e9b69e |

## 表示QAで修正した説明

一致がない確定結果と、前提拒否／停止時の未確定結果を分けて表示した。初期例も1,3,5 / 3にして境界誤りをすぐ比較できるようにした。

範囲説明を精密化した。`[lo, hi)`は反復で調べる未確定indexであり、lower boundの挿入位置pは`lo ≤ p ≤ hi`に残る。hiの位置に一致値があっても正しい。古い説明で「候補」とだけ書くと両者を混同するため、この違いを予想・凡例・答えへ追記した。search.jsの実装は不変で、変更したHTMLのdigestでNode観測を取り直し、Browserをreloadして最終説明と候補消失例を確認した。以前のNode観測2件・画像は保持している。

## Skillの限定確認

[Skill](skills/atlas-algorithms-data-structures/SKILL.md)に、実装・UI・検査・生記録とscopeへの相対参照を設けた。skill-creatorの簡潔な発見情報とscope保持を適用し、既存コードを再利用する入口にした。

```sh
python3 /path/to/skill-creator/scripts/quick_validate.py skills/atlas-algorithms-data-structures
```

実際の出力は `Skill is valid!`。name／frontmatterの検査と全相対参照の実体確認が成功。

同じ担当による軽いcontrol例：「1,3,3,5から3の最初の位置」を既存search.jsへ渡し、index1・3反復を実観測。「重み付きGraphの最短路をこの教材で実装」という依頼にはscopeを読み、この教材は未対応、Graphは未教材と案内する判断を確認した。[control記録](observations/skill-control.json)に出力とSkill digestを保存。独立AgentのForward Evalや全Subject Skill完成の証拠ではない。global installは行っていない。

## Sourceと未確認

- search.js：`ac40be53ace504204ed91200daa6243a91b629efa2bad91aa7402cee3a245516`
- index.html：`bc3f0ec8c2d20fca445cda233c1694482a7f70c1cd333ad4e51d69deeced8341`
- 最終Node生記録：`659f7c596eeee9a4ef818c12f79693fcfb409789d5a14f01f71e1bc883b1f670`
- Browser生記録：`81f353a08cd710ee0a941dcef06e0dd3a35d7e5b54f7eda4e885d8c6a444ff44`

実装版・入力・環境・時刻・digestは生記録に含む。現在の4 Sourceファイルは最終Node記録のdigestと一致した。差分／JS構文も確認した。実観測のない実行metadataを補っていない。

file URL、狭幅viewport、支援技術、実タッチ、多Browser比較、学習者評価は未実施。最大32要素・固定数値比較の説明モデル。Graph／DP／tree等はscope表とscope.jsonへ未教材として残す。

編集はこのmodule内のみ。元Frontend repoやPortalのroot README／docsを編集していない。Docker・kind・emulator・GPUは使用せず、背景タブと一時serverを終了する。公開・commit・pushなし。この1本の確認を全Subject完成へ読み替えない。
