---
name: atlas-cyclic-module-read-timing
description: 既存Node native ES modulesのA↔B循環で即時readと初期化後の関数readを実行する有限教材。TLA/bundler/browserrealm/URLcache/fullspecには使わない。
---
元frontend live binding→本README/固定表→Node原票→static-name-resolutionを辿る。固定graph/event/class/final表はproducer前に置き、oracleはproducerをimportせずliteral照合する。
ケースごとにnew child processを作る。即時B読取は未初期化A bindingのReferenceError。関数にしただけでB評価中にcallしても拒否、entry初期化後callなら1。acyclic/live更新を対照にする。
console logを観測eventとして扱い、engine内部linker/DFS/statusは採取したと主張しない。実例外name/message・child exit1とbatch exit0を分ける。private stack/pathを保存しない。
UIは保存reader。全予想select/数値editable変更は新値保持、旧比較/trace/答え本文を空にしdetailsを閉じる。case変更は予想条件reset。予想入力拒否と実Node ReferenceErrorを区別する。
通常checker/runnerはhash/mtime不変。明示--recordだけfresh run/source snapshotを作り旧raw保持。上記excludedや公開/install/設定変更へ広げない。
