# Atlas：この教材を読む順

1. 変数A〜Dへ色0/1を選ぶこと、無向辺の両端は異なることを確認します。
2. 部分割当から次の変数へ進み、戻って別候補を試す深さ優先探索を前提にします。
3. [手計算](HAND_TRACE.md)で全16割当と有効集合を確認します。
4. [契約](CONTRACT.md)と[疑似コード](PSEUDOCODE.md)でdomainとassignment、候補snapshotとtrailを分けます。
5. 保存結果の画面で削除→成功/矛盾→復元→次候補を辿り、[Skill](SKILL.md)の問いへ進みます。

## 既存教材との関係

以下は既存workspace内の出所です。この教材だけのHTTP配信から外部ディレクトリへ戻れるリンクとはしていません。位置とSHAは[出所記録](records/prerequisite-sources.json)で確認できます。

- 元 artificial-intelligence-foundations：BFS/A*・固定格子の到達と経路。
- weighted-search-cost：重み付き経路、優先queueと全単純経路の照合。README:47/COVERAGE:7に残るCSPの問いを今回扱います。
- register-history-linearizability：後戻り探索とprefix枝刈りが既にあります。今回の新しい問いは有限domainの削減・復元・全解集合です。
- orchestration-taint-selector-eligibility：条件による候補nodeの絞込み。今回の枝ごとのdomain復元とは別です。

このページだけでも前提を確認できるよう、集合を残り候補、assignmentを現在選んだ値、trailを削除値を戻すための記録として説明します。探索順A,B,C,Dは固定で、変数順選択の最適化は扱いません。
