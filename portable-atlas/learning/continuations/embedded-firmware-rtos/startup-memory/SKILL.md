---
name: atlas-embedded-startup-memory
description: Atlasの16 byte ROM/RAM模型で、配置先・dataコピー・bssゼロ化・早期読取りを分けて学ぶ。実firmwareやlinker、MCUの検証には使わない。
---

# Atlas — 起動メモリーの問いを案内する

[README](README.md)の前提と[契約](CONTRACT.md)を先に読む。[画面](index.html)で予想し、保存計算を開いて次の比較へ進む。byte/offset/半開区間に迷う場合はREADMEのTiny8・組込み入口へ戻る。このSkillは教材の案内で、実deviceの操作や共有設定の変更を許可しない。

- 「ROMに初期値があるのになぜRAMへcopyするか」にはLMA/VMAの2領域図、copy-zero-mainとskip-copy、[GNU ldとの対応](SOURCE-MAP.md)を案内する。配置の指定と実行時の書込みを分ける。
- 「copyとzeroは必ずこの順か」にはcopy-zero-mainとzero-copy-mainを比較する。今回の非重複範囲で両方が正しいことを示し、重複する任意の範囲へ広げない。
- 「最後のRAMが正しければ起動成功か」にはmain-earlyを案内する。その時の読値はA5のままで、後の初期化が過去の観測を書き換えない。
- 「変数の値が合っていれば越境はないか」にはcopy-one-pastを案内する。ROM offset8からRAM guard6への余分な1 writeを全履歴・全RAMで確認する。
- 「空領域で成功したが何を初期化したか」にはempty-regionsを案内する。0 byteの契約達成とwrite0、空配列を説明し、4 byteのcopy成功と混同しない。

予想→正常と故障の対照→手表・実装・原典→答え→実務判断の順を守る。数値の根拠は[保存計算](observations/calculation-20261006T214619487663Z/result.json)と[検査結果](observations/saved-verification.json)、固定した[手表](hand-oracle.json)へ結ぶ。[COVERAGE](COVERAGE.md)にある実機起動、linker出力、flash、HAL、RTOSや安全性の要求には、この有限模型で検証済みとは答えない。実計算・画面の確認状況はREADMEと[画面確認](GUI-QA.md)の現在状態を確認してから説明する。
