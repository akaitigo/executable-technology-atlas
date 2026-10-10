# tick stateを汚さず描画を補間する

元Subject E3のrender interpolationに絞った有限単位。20ms tickで位置を20 toy unit増やす。合成frame列[25,15]では最初のprevious0/current20・余り5・alpha1/4・描画5。正常はcurrent20を保持し、次tickはcurrent40。描画5を書き戻す故障では次tick current25に汚れる。既存の自由落下・衝突教材と独立した実装。

このdirectoryで `node server.mjs` を実行し、表示された専用127.0.0.1 URLを開く。予想→実frame描画→正常/書戻し故障比較→source/raw→答えと実務判断。予想2欄と条件JSONの変更で結果・答え・Canvasを消す。条件変更は入力も初期化する。実描画後の結果保留と古い結果の無視を操作できる。

JSONは全置換 `{ "framesMs": [27,13], "mode": "NORMAL" }`。framesは1..8個の整数0..100ms、modeはNORMAL/FAULT_WRITEBACKのみ、追加key拒否。全frameを検証してから更新する。固定15＋可変4条件の全traceを、実装をimportしないPython Fraction oracleと実行前literalへ照合する。`node runner.mjs normal-5`、`python3 -B record.py` はread-only。新規原票は `python3 -B record.py --record` のみ明示write。過去原票は上書きしない。

Canvasの各frameは実rAF callbackで描く。rawにcallback timestamp、wallUTC、合成ms、描画座標、中心pixel RGBAを別々に保存する。合成時間からtick数を決めるため、rAF間隔・実latency・FPS・物理精度・実ゲームengine・input/audio/release budgetは測定しない。正常のalpha0はpreviousを描くのでcurrentと同じでなくても誤りではない。位置の厳密分数とpixel丸めも区別する。

[実行前期待値](EXPECTATIONS.md)、[producer](producer.mjs)、[独立oracle](oracle.py)、[一次資料](SOURCES.md)、[現在原票](evidence/current.json)、[Browser証拠](evidence/browser.json)、[検証結果](evidence/verification.json)、[有限Skill](skills/atlas-render-interpolation/SKILL.md)。Scopeはこの単位のみ。Subject・Atlas全体はincomplete、Core/fullGate未実施。
