# ストレージ・ファイルシステム工学：今回の対応範囲

元計画は既存Atlasの <code>learning/subjects/storage-filesystem-engineering/COVERAGE.md</code>、第1行「次1」の **sparse fileのlogical/allocated size** です。元ファイルの内容・入口・manifestは変更していません。このフォルダーは既存作者の作業ファイルと分けた一時的な制作先です。

現在の分野ゴールは`2026-10-06/task-8/atlas-97-field-goals-ja.md`の14番です。「保存済み疎ファイル教材の差分と局所受入を元担当へつなぐ」に沿い、同じwriterがこのpathだけを修理・検査しています。accepted90とpost90 37の正式identity照合では、storageの追加受入はconcurrent-update-lockingであり、このsparse単元は127へ未加算でした。元repoのowner現在稼働は不明のまま、台帳・元repoは変更しません。

| 元計画の論点 | 今回の根拠 | 状態・残る問い |
|---|---|---|
| sparse fileのlogical/allocated size | expected.json、experiment.py、observations/run.json、37項目の検証 | Macの小さい新規通常ファイル2個について確認 |
| ファイル位置と論理長 | seek65,535後の長さ0と空の読取り、書込み後の長さ65,536 | truncate・appendモードとの比較は未教材 |
| ファイル内の穴とEOF | 全65,535ゼロ+Xの保存読取り、先頭と末尾・EOFの別読取り | 穴の物理配置は未観測、SEEK_HOLE/SEEK_DATAは未検証 |
| 通常書込みとの比較 | 全内容一致、st_blocksを独立に保存 | 割当差が出ることは保証しない。コピー時の穴保存は未検証 |
| 同じ「次1」のhardlink/unlink/open FDの寿命 | 本単元には含めない | 既存の別単元の受入状況に従う。ここでは追加達成扱いしない |
| 同じ「次1」のreplace時metadata・symlink・permission拒否 | 本単元には含めない | 次の独立課題 |
| 次2：並行writer・lost update・network filesystem | 本単元には含めない | 未教材範囲として維持 |
| 次3：sync・crash consistency・電源断・性能 | fsyncを呼ばず、永続性・性能の証明をfalseに固定 | この観測からは判断不可 |
| 次4：block配置・CoW・snapshot・実媒体 | st_blocksを観測時点のOS報告値として示す | 実デバイスの物理配置や予約、APFS内部は未実証 |
| 日本語の視覚教材・再現手順・再利用Skill | index.html、file-layout.svg、README.md、SKILL.md | 初回5検査/4画像は履歴保持。現readerは3条件・15検査pass、1280/390pxの実画像7枚目視。42実pointer・11文字入力と選択API6回を分離 |
| 予想・reset・資料照合 | 古いraw/比較表/答えの消去、初回digest待機、欠落/改変からの再読込 | 現GUI原票で確認。native dropdownの手操作は未確認。2回のキー操作harness停止も保持 |
| Atlasの検索・既存入口への統合 | なし | 未統合。受入数・分野数への加算は調整担当が判断 |

全分野・当分野の全知識を網羅したとは扱いません。実装と保存観測の検証、実画面の検証、Portal統合は別の状態です。

現readerの予想変更・resetの修理、GUI検査と別reviewerの独立受入は[状態記録](observations/status.json)へ記載します。初回37検証と共有GUI原票は履歴として保持し、OS実験を再実行しません。

現GUIの根拠は[原票](browser-qa/run-2026-10-06T072414863Z/report.json)、[実画像の目視](browser-qa/visual-review.json)、[修正前後・失敗履歴・最終binding](browser-qa/gui-revision-20261006T071437683122Z/final-binding.json)です。自動操作APIの条件変更を実ポインター操作と呼びません。
