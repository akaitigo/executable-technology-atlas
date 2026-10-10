// 未コンパイル・未実行。固定SDKの公開APIで組み立てた実Widget候補。
import 'package:flutter/rendering.dart' show ScrollCacheExtent;
import 'package:flutter/widgets.dart';

enum LookupMode { withLookup, withoutLookup }

class ProbeRecorder {
  int nextId = 0;
  late ProbeHostState host;
  final events = <Map<String, Object>>[];
  final builds = <Map<String, Object>>[];
  final lookups = <Map<String, Object?>>[];
  final live = <String, CounterTileState>{};
}

class ProbeHost extends StatefulWidget {
  const ProbeHost({required this.mode, required this.recorder, super.key});
  final LookupMode mode;
  final ProbeRecorder recorder;
  @override
  State<ProbeHost> createState() => ProbeHostState();
}

class ProbeHostState extends State<ProbeHost> {
  final order = <String>['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'];
  final controller = ScrollController(keepScrollOffset: false);

  @override
  void initState() { super.initState(); widget.recorder.host = this; }

  int? indexFor(Key key) {
    final item = key is ValueKey<String> ? key.value : null;
    final index = item == null ? -1 : order.indexOf(item);
    widget.recorder.lookups.add({'itemId': item, 'index': index < 0 ? null : index});
    return index < 0 ? null : index;
  }

  void swapFirstTwo() => setState(() {
    final first = order[0]; order[0] = order[1]; order[1] = first;
  });

  void increment(String itemId) => widget.recorder.live.values
    .singleWhere((state) => state.widget.itemId == itemId).increment();

  List<CounterTileState> tilesInTreeOrder() {
    final found = <CounterTileState>[];
    void visit(Element element) {
      if (element is StatefulElement && element.state is CounterTileState) {
        found.add(element.state as CounterTileState);
      }
      element.visitChildren(visit);
    }
    context.visitChildElements(visit);
    return found;
  }

  @override
  Widget build(BuildContext context) => Directionality(
    textDirection: TextDirection.ltr,
    child: Align(
      alignment: Alignment.topLeft,
      child: SizedBox(
        width: 320, height: 160,
        child: ListView.builder(
          controller: controller, primary: false,
          physics: const ClampingScrollPhysics(),
          padding: EdgeInsets.zero, itemExtent: 80, itemCount: order.length,
          scrollCacheExtent: const ScrollCacheExtent.pixels(0),
          addAutomaticKeepAlives: false,
          findChildIndexCallback:
            widget.mode == LookupMode.withLookup ? indexFor : null,
          itemBuilder: (context, index) {
            final itemId = order[index];
            widget.recorder.builds.add({'index': index, 'itemId': itemId});
            return CounterTile(key: ValueKey<String>(itemId),
              itemId: itemId, recorder: widget.recorder);
          },
        ),
      ),
    ),
  );

  @override
  void dispose() { controller.dispose(); super.dispose(); }
}

class CounterTile extends StatefulWidget {
  const CounterTile({required this.itemId, required this.recorder, super.key});
  final String itemId;
  final ProbeRecorder recorder;
  @override
  State<CounterTile> createState() => CounterTileState();
}

class CounterTileState extends State<CounterTile> {
  late final ProbeRecorder recorder;
  late final String stateId;
  late final String mountedFor;
  int count = 0;
  String get label => '項目 ${widget.itemId} / State $stateId / 生成時 $mountedFor / 回数 $count';

  void record(String event, {String? previousItemId}) => recorder.events.add({
    'event': event, 'stateId': stateId, 'itemId': widget.itemId,
    'mountedFor': mountedFor, 'count': count,
    if (previousItemId != null) 'previousItemId': previousItemId,
  });

  @override
  void initState() {
    super.initState(); recorder = widget.recorder;
    stateId = 'S${++recorder.nextId}'; mountedFor = widget.itemId;
    recorder.live[stateId] = this; record('initState');
  }
  void increment() => setState(() { count++; record('increment'); });
  @override
  void didUpdateWidget(CounterTile oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (!identical(recorder, widget.recorder)) throw StateError('Recorder changed');
    record('didUpdateWidget', previousItemId: oldWidget.itemId);
  }
  @override
  void deactivate() { record('deactivate'); super.deactivate(); }
  @override
  void dispose() { record('dispose'); recorder.live.remove(stateId); super.dispose(); }
  @override
  Widget build(BuildContext context) => GestureDetector(
    onTap: increment,
    child: ColoredBox(
      color: const Color(0xFFF0F5FF),
      child: Center(child: Text(label,
        style: const TextStyle(fontSize: 14, color: Color(0xFF172238)))),
    ),
  );
}
