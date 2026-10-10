# Atlas｜書込fieldと拒否時の変更を案内する

このローカルSkillは [学習画面](index.html) の保存された24要求の説明に限定します。[再現手順](REPRODUCE.md)、[契約](CONTRACT.md)、[実装前の要求](cases.json)、[手書き期待](expected.json)、[保存結果](observations/run-01/results.json)、[原典](SOURCES.md)、[範囲](COVERAGE.md) を辿れます。自動インストールや一般Agent能力の評価ではありません。

1. [読取field教材](related.html?topic=read-field)を前提に、read grantとwrite grantを分けます。上流contextの真正性は仮定であると伝えます。
2. operator-titleで修正版の許可と、途中検査方式のstore変化を別々に予想してもらいます。
3. allowed-then-forbiddenを開きます。403でもtitleが変わった対照を、応答payloadとstore差分を分けて読みます。
4. forbidden-then-allowedと比べ、先に拒否された場合だけ不変でも十分ではないと確認します。
5. 修正版は全fieldの許可を検査してから反映することを、実行時コードと [原典対応](SOURCES.md)で説明します。
6. 対象recordの指定fieldだけの変更、拒否時のstore全体不変を答え合わせし、実DBの保証とは分けます。

資料を利用する有限な3問は次のとおりです。

- 「読めるviewerなら更新できる？」→いいえ。[保存結果](observations/run-01/results.json) のread-not-writeはwrite grantなしで拒否。[書込許可表](fixture.json)の別grantを読みます。
- 「403なら何も変わっていない？」→いいえ。allowed-then-forbiddenのincremental_checkはtitleが変わります。[手書き期待](expected.json)のchangedFieldsと保存した全afterStoreを確認します。validate_then_applyは拒否時不変です。
- 「この置換で実DBの同時更新やrollbackも安全？」→今回の証拠では判断できません。[範囲](COVERAGE.md)へ戻り、DB transaction・並行競合・永続化の試験が別途必要だと伝えます。

取得失敗・内容不一致では古い比較を使いません。未知の実システム・資格情報や本番への操作要求へ拡張せず、未実装範囲を明示します。

関数比較と独立照合に加え、画面の14項目・24要求/72応答の実DOM・実画像9枚を確認しました。[操作記録](qa/run-2026-10-06T163439899Z/report.json)、[作者目視](qa/self-visual-review.json)、[独立受入の状態](qa/reader-acceptance.json)を分けて参照してください。3問の資料利用を、一般Agent能力の確認へ広げません。
