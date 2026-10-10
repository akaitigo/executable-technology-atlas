# Atlas：形式手法の中の今回の範囲

分野目標04（task-8 `atlas-97-field-goals-ja.md`:82–91）と、元 `executable-technology-atlas/learning/subjects/formal-methods-verification/LEARNING_PATH.md` §5/§6実験1の「公平性と飢餓」に対応します。元 `COVERAGE.md` も参照専用です。これらはworkspace内の出所で、教材単体のHTTP配信先からは解決しません。[元モデルの場所・差分範囲](records/input-and-dedup.json) と [同梱した完全copy](inputs/prerequisite-model.py) を使って照合できます。

|問い|今回の材料|境界|
|---|---|---|
|相互排他を守る状態と辺|旧atomicモデルの完全copy、8状態/14辺|旧正常対照を新しい成果として数えない|
|何が選べて、何を選んだか|6列のprefix/cycle・出発状態のenabled/executed|実schedulerの測定ではない|
|弱公平性と強公平性の対象|Next0/Next1とEnter1、4仕様|任意のPlusCal fair processとの同一視なし|
|要求後の進行|各waiting位置から後のcriticalを追う|以前の入室は後の要求を満たさない|
|公平でも進まない境界|保持中の停滞はSF入室1のみで許される|P0.releaseが有効なのでdeadlockではない|
|画面とSkill|状態記録から実DOM・画像・独立確認へ|一般Agent能力や全ブラウザーの保証ではない|

旧2lock教材はdeadlock/livelock、旧ループ教材は不変条件/終了という別の問いです。[調査範囲と出所](records/input-and-dedup.json) を保存しました。全PCの教材不存在や、元共有owner不在は断定していません。

Atlas の未対応は、任意の全fair cycleの探索・一般の飢餓自由定理・公平性仕様の実装への精緻化・任意process数・故障・弱メモリー・実時間上限です。次の問いは「全ての公平な周期を対象にするなら、どの性質を追加で証明する必要があるか」。今回の6例から答えを補完しません。新しい教材や実行は、この問いの提示だけで自動的に始めません。
