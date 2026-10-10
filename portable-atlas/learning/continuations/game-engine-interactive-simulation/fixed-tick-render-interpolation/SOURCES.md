# 一次資料と独自実装

- [Glenn Fiedler, Fix Your Timestep!](https://gafferongames.com/post/fix_your_timestep/) (2004-06-10, 2026-10-06確認)。前/現stateをaccumulator比で補間し描画へ渡す設計を参照。この記事のcodeはコピーしていない。今回の20ms/20unit・整数合成delta・書戻し故障・有理数実装は独自toy。
- [HTML Living Standard — Animation frames](https://html.spec.whatwg.org/multipage/imagebitmap-and-animations.html#animation-frames) (2026-10-05更新, 2026-10-06確認)。rAF callbackのtimestampは描画呼出し記録として保存し、fixture deltaの代替にしない。
- [CanvasRenderingContext2D getImageData](https://html.spec.whatwg.org/multipage/canvas.html#dom-context-2d-getimagedata)：実Canvasのmarker中心RGBAを読み出す。位置のpixel丸めは40+round(render×scale)、scale=min(4,760/max論理位置)、論理位置の厳密有理数と区別する。

図はBrowser Canvas APIによる独自生成。外部画像、ゲームengine、追加依存なし。元Subject README E3のinterpolationのみを増分として扱い、既存physics刻み・floor判定へ変更を加えない。
