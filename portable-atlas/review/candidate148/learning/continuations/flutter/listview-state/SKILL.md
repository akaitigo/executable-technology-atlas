---
name: flutter-listview-state
description: ListView.builderの遅延生成と並べ替えについて、項目Key・findChildIndexCallback・Stateの生存範囲を予想し、固定ソースと保存済みの実Widget原票で確認する。
---

# ListViewのState対応を確認する

このSkillは本教材内で使うローカル手順です。インストール・公開済みSkillではありません。**固定SDKの2条件×5段階を局所受入し、保存実測readerのブラウザー操作・画像QAも確認しています。事前予測・実Widget原票・reader画面は別資料です。FlutterライブGUIは未確認です。**

## 適用する場面

遅延生成される一覧を並べ替えたとき、安定Keyを付けても子のStateが失われる理由を調べたい場合に使います。Column直接兄弟の一般的なKey導入だけなら前単元を参照します。GlobalKey・復元・keep-alive設計全体を本単元で説明済みにはしません。

## 手順

1. [README](README.md)と[COVERAGE](COVERAGE.md)を読み、対象fixtureと未対応範囲を確認する。ListView利用の有無と、State対応の教材化の有無を区別する。
2. 答えを見る前に、初期生成対象、先頭入替後のStateと回数、遠方へ移動して戻ったときの回数を予想する。
3. [expectations.json](expectations.json)を開き、2条件の差がcallbackだけであること、cache 0・keep-aliveなし・子State内の回数という制限を確認する。固定表は実行前の予測で、今回の原票と一致しても一般的な生成数の保証にはならないと伝える。
4. [固定ソース対応](source-map.json)と`indexFor`を読み、Key→現在index→保持中のElementの関係を説明する。callbackが破棄済みStateの保存機構ではないことを説明する。
5. [REPRODUCE](REPRODUCE.md)の`python3 serve.py`でreaderを開き、条件と予想を選び、保存実測を再生する。同時点の対照、原典・実行時ソース、答え合わせの順で確認する。これは保存原票の選択・再生で、Flutterライブ操作ではないと伝える。条件/予想変更やresetで古い答えが消えることを確認する。
6. 行表示だけでなくState識別子・builder呼出・生成/破棄を分けて比べる。[別Pythonチェッカー](probe/verify_observation.py)で実行を重ねずに原票を照合できる。不一致・途中失敗も保存し、失敗attemptの上書きや、予測を観測扱いする書換えをしない。
7. 「生存中の入替対応にはKeyとcallback」「破棄をまたいで必要な業務データには別の所有者」という判断を述べ、未検証のkeep-alive比較・FlutterライブGUI・復元を残す。

nativeやGUIの再検証が必要な場合だけ、再現手順の全体資源条件と担当間の実行枠を確認します。初回成功の確認を重ねるためだけにcompiler/browserを起動しません。readerの確認済みGUIと、未確認のFlutterライブGUIを区別します。

## 記録の返し方

専有path、扱った条件、静的確認の範囲、実行の有無、原票がある場合はそのpathと差分、未対応範囲を短く報告します。Python ASTの成功をDartのcompile成功に換算しません。実Flutterのprogrammatic probe、headless raster、通常GUI/pointer、保存実測readerはそれぞれ別の証拠として扱います。
