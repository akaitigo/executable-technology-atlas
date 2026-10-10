# Atlas：原典と今回の選択

Robert Nystromの著者本文を2026-10-06に読取りました。書籍サイト本体の2ページは各1回400で取得できず、著者のGitHub本文へ進みました。[取得記録](sources/retrieval.json)を保持し、可変のmasterを固定commitとは呼びません。

|著者本文のlocator|今回の読解|
|---|---|
|[A Virtual Machine / A Value Stack Manipulator](https://raw.githubusercontent.com/munificent/craftinginterpreters/master/book/a-virtual-machine.md)、320–329 / 376–382|左、右、親の後順を命令列へ写し、一時値をstackで渡す|
|同 Stack tracing、507–528|命令に沿ってstackを読み、定数のloadが値を積むことを追う|
|同 Binary operators、657–664|右側が先にpopされ、その次が左側。値の一致と順序の確認を分ける|
|[Chunks of Bytecode / Constants](https://raw.githubusercontent.com/munificent/craftinginterpreters/master/book/chunks-of-bytecode.md)、590–650|定数値を表へ置き、命令のindexから参照する|

Atlasでは、Cとdoubleの実装をコピーしません。Python整数、JSONの構造化命令、命令番号pc、定数の初出順重複除去、明示的な不正入力拒否は今回の独自契約です。byte encoding、機械語、関数returnや実Loxとの互換性は対象外です。原文全文・図の転載は行っていません。

前提の元 [language.py](inputs/prerequisite-language.py) はローカル教材の完全一致コピーです。新producerはその木評価器を再利用し、VMと別の評価経路を保ちます。元教材の位置とSHAは [input-provenance.json](records/input-provenance.json) に保存しています。
