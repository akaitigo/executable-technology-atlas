// 制作時点では未コンパイル・未実行。実結果は別の観測原票へ保存する。
import 'package:flutter/rendering.dart';
import 'package:flutter/widgets.dart';

enum KeepMode { requested, notRequested }

class Recorder {
  int nextId = 0;
  late HostState host;
  final live = <String, TileState>{};
  final events = <Map<String, Object>>[];
  final builderCalls = <Map<String, Object>>[];
}

class Host extends StatefulWidget {
  const Host({required this.mode, required this.recorder, super.key});
  final KeepMode mode;
  final Recorder recorder;
  @override
  State<Host> createState() => HostState();
}

class HostState extends State<Host> {
  final items = <String>['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'];
  final controller = ScrollController(keepScrollOffset: false);
  @override
  void initState() { super.initState(); widget.recorder.host = this; }
  void increment(String id) => widget.recorder.live.values
    .singleWhere((tile) => tile.widget.itemId == id).increment();

  List<TileState> tilesInElementTree() {
    final result = <TileState>[];
    void visit(Element element) {
      if (element is StatefulElement && element.state is TileState) {
        result.add(element.state as TileState);
      }
      element.visitChildren(visit);
    }
    context.visitChildElements(visit);
    return result;
  }

  @override
  Widget build(BuildContext context) => Directionality(
    textDirection: TextDirection.ltr,
    child: Align(alignment: Alignment.topLeft, child: SizedBox(
      width: 320, height: 160,
      child: ListView.builder(
        controller: controller, primary: false,
        physics: const ClampingScrollPhysics(), padding: EdgeInsets.zero,
        itemCount: items.length, itemExtent: 80,
        scrollCacheExtent: const ScrollCacheExtent.pixels(0),
        // 両条件とも祖先AutomaticKeepAliveを付け、子の要求だけを変える。
        addAutomaticKeepAlives: true,
        itemBuilder: (context, index) {
          final item = items[index];
          widget.recorder.builderCalls.add({'index': index, 'itemId': item});
          return Tile(key: ValueKey<String>(item), itemId: item,
            keep: widget.mode == KeepMode.requested, recorder: widget.recorder);
        },
      ),
    )),
  );
  @override
  void dispose() { controller.dispose(); super.dispose(); }
}

class Tile extends StatefulWidget {
  const Tile({required this.itemId, required this.keep, required this.recorder, super.key});
  final String itemId;
  final bool keep;
  final Recorder recorder;
  @override
  State<Tile> createState() => TileState();
}

class TileState extends State<Tile> with AutomaticKeepAliveClientMixin<Tile> {
  late final Recorder recorder;
  late final String stateId;
  late final String mountedFor;
  int count = 0;
  @override
  bool get wantKeepAlive => widget.keep;
  bool get keepRequested => wantKeepAlive;
  String get label => '項目 ${widget.itemId} / State $stateId / 回数 $count';
  void record(String event) => recorder.events.add({
    'event': event, 'stateId': stateId, 'itemId': widget.itemId,
    'mountedFor': mountedFor, 'count': count, 'wantKeepAlive': wantKeepAlive,
  });
  @override
  void initState() {
    super.initState(); recorder = widget.recorder;
    stateId = 'S${++recorder.nextId}'; mountedFor = widget.itemId;
    recorder.live[stateId] = this; record('initState');
  }
  void increment() => setState(() { count++; record('increment'); });
  @override
  void didUpdateWidget(Tile oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.keep != widget.keep) {
      // この実験中の要求は不変。動的切替の比較は別単元に残す。
      throw StateError('固定条件のkeep値が変化しました');
    }
    record('didUpdateWidget');
  }
  @override
  void deactivate() { record('deactivate'); super.deactivate(); }
  @override
  void dispose() { record('dispose'); recorder.live.remove(stateId); super.dispose(); }
  @override
  Widget build(BuildContext context) {
    super.build(context); // mixinとの契約。戻り値は使用しない。
    return ColoredBox(color: const Color(0xFFF0F6FF),
      child: Center(child: Text(label,
        style: const TextStyle(fontSize: 14, color: Color(0xFF162C3C)))));
  }
}
