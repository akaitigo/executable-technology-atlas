# 実Browser原票と読み取り専用検査

入力・手表を先に固定し、binary.jsが72byteを生成、runtime.jsが実Browser WebAssembly.instantiate/export/memory.growを実行する。Browser rawのUTC、input、段階、例外class/message、実byte列とSHA-256をIAB DOMから手転記。入力reset修正後の7件再実行は全非時刻fieldの一致をtoolで検査し、実返却UTCへ更新した（transcription-provenance.json）。browser-transcriptとhost-invalid-transcriptを保ち、明示record時に新attemptへ包む。Pythonのexit0は保存証拠のchecker成功でありBrowser process exitではない。engine build版はtoolで公開されず不明。

oracleはBrowser/Wasm/JS producerを使わず、別literal hexと固定page/address/byte/例外表で照合。byte sectionのtype/function/memory/export/codeも読む。原票改変6種を拒否。通常checker/routeの全file hash/mtimeを前後比較し、proofは最後だけ書く。初回receiptと実rawを保ち、UI QA後に現source/artifactをsealする。

実IABは7条件、予想4選択への単独変更（毎回成功比較→答えを開く→予想だけ変更）、条件reset、位置3拒否、host8拒否、成功後基盤失敗、旧保留応答の非採用、原教材・関連・実装・手表・oracle・READMEの導線を検査する。captureは実ツール画像のみ、ローカル保存可否は別記録。再構成画像をcaptureと呼ばない。所有server/tabだけ閉じ、他owner listenerを変更しない。
