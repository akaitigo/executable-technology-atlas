# keyの寿命とgeneration CAS

問いは「versionがあれば、削除・再作成されたkeyへの古い要求も拒否できるか」です。Operational data storesのLEARNING_PATH §6実験1だけを扱い、専用SQLiteで実conditional UPDATEを固定順に実行します。

## 前提 → 予想 → 操作

key/value、WHERE、更新行数、version、状態遷移を前提とします。1条件1connection、逐次autocommit。g1→g2は合成・非再利用tokenの有限契約です。実分散generation発行器はありません。

1. 単元directoryで `python3 checker.py`。手書き状態表・SQL原票・read-only DB snapshotを検算します。
2. `python3 -m http.server 0 --bind 127.0.0.1`。未使用の動的port URLでindex.htmlを開き、条件と予想を選び「比較する」。所有serverだけ終了します。
3. UPDATE rowcountと各時点のgeneration/version/valueを追い、SQL・原票を読んで答えを開きます。条件切替で予想・結果・答えをreset。
4. 再実行は明示 `python3 runner.py --record`。専用TemporaryDirectoryで11 DBを作り、closeしたsnapshotとSQL traceを新observationsへ保存し、tmpをcleanup。旧原票は保全。通常runnerは書かずexit1で案内します。

予想は同世代v1→v2後の古v1が両方式で0行。delete/recreateでg2/v1になればversion-onlyは旧g1/v1要求を1行更新、generation+versionは0行です。新g2の要求は1行になります。

## 手書き状態表と実更新

`expected-states.json`をproducer実行前に固定しました。schemaはkey TEXT PRIMARY KEY, generation TEXT, version INTEGER, value INTEGER。固定key k、初期g1/v1/value0です。

| schedule | 途中state | 旧要求rowcount / 直後state | 新要求rowcount / 最終state |
|---|---|---|---|
| 同世代 version-only | g1/v2/5 | 0 / g1/v2/5 | 1 / g1/v3/6 |
| 同世代 generation+version | g1/v2/5 | 0 / g1/v2/5 | 1 / g1/v3/6 |
| delete/recreate version-only | absent → g2/v1/100 | 1 / g2/v2/1 | 1 / g2/v3/101 |
| delete/recreate generation+version | absent → g2/v1/100 | 0 / g2/v1/100 | 1 / g2/v2/101 |

version-onlyは `WHERE key=? AND version=?`、正常な世代保護版は `WHERE key=? AND generation=? AND version=?`。SETはvalueとversion+1だけで、generationを変更しません。再作成時のg2はINSERTで与えます。古い要求が通るversion-onlyを教育用の故障対照とします。

入力契約はkey='k'、generation='g1'/'g2'、versionはboolを除くint1〜999、valueはboolを除くint0〜999。6拒否fixtureはUPDATEを発行せずstate保持。SQL構文errorの1probeはOperationalError・rowcount=nullを保存し、WHERE不一致0行と別にします。通常caseのSQL成功と更新拒否を「実験失敗」と混同しません。

## 原典・実装・原票・独立oracle

- [SQLite UPDATE §2](https://www.sqlite.org/lang_update.html)：WHEREが真の行だけ更新。対象0行はSQL errorではない。
- [Python sqlite3](https://docs.python.org/3.9/library/sqlite3.html)：Cursor.rowcount / isolation_level=None。取得Docs3.9.25と実行版は分けます。

experiment.pyの実SQLをtrace callbackで保存し、各stepのSQL template/params/rowcount/before/stateを採取。runnerはcommand stdout/stderr/exit・runtime・source hashes・11実DB・artifact hashesを保存します。UIは保存原票の比較で、閲覧時の新SQL実行ではありません。

checker.pyはproducerをimportせず、手書きstate/rowcount表と独立request tuplesへ照合します。11保存DBをmode=ro&immutable=1で開き、最終SELECTを別経路で読む。5つのin-memory故障原票（旧世代受理・generation消失・version再利用隠し・拒否を成功化・SQL errorを0行化）を検出し、正規rawは変更しません。

[QA](qa/README.md)に実IAB/captureとread-only検証を保存。Skillはskills/atlas-key-generation-cas/SKILL.md、正常7/未対応4routeは構造検査のみ。モデルの選択・実行挙動は未評価。

## 答え → 実務判断

versionは更新履歴を区別しても、再利用されたversionが以前と同じkey lifetimeを意味するとは限りません。key再作成を認める設計では非再利用generationも条件に含めます。0行なら勝手に成功扱いせず、再読取り・再計算の方針を別途定めます。

g1/g2の非再利用はfixtureの前提。分散発行、backup復元後の重複、実並列locking、crash/power loss durability、replication、実分散CASは未実証です。保存DBは最終状態の証拠で、電源断復旧の保証ではありません。

## 次coverage（未実行）

1. 古計算の再送と再読取り・再計算、応答消失とrequest IDでの業務重複対照。
2. fake clockでTTL直前/同時/直後と、原本更新後のcache staleを比較。
3. 2key総和の不変条件をautocommit途中失敗とtransaction rollbackで比較。

Core/fullGate/commit/push/公開はローカル割当外で未実行。有限単元の結果から分野全体・Atlas全体のcompleteを主張しません。
