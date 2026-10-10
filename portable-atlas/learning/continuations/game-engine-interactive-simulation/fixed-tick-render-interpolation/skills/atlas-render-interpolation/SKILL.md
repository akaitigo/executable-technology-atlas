---
name: atlas-render-interpolation
description: この有限教材で20ms tick stateとrender interpolationの分離・書戻し故障を学ぶ。実engine精度、FPS、latency、audio/inputの検証には使わない。
---

教材rootはこのSkillの2階層上。`python3 -B route.py interpolation` でREADME、`compare`でEXPECTATIONS、`verify`でchecker、`sources`で一次資料へ進む。予想→操作→正常/書戻し故障→全frame trace/Canvas→実raw→答え。任意JSONは全置換、可変remainderでも答えは実traceから導出する。描画値とtick state、合成msとrAF timestamp、厳密分数とpixel丸めを区別する。記録は明示--recordのみ。元Subject E3全体やphysics精度を完了と扱わない。未対応routeはunsupportedを返す。
