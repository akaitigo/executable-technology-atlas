// 制作時点では未実行。実測は独立したattempt原票に保存する。
import 'package:flutter/widgets.dart';

enum MoveMode { globalSameFrame, globalGap, valueSameFrame }

class Recorder {
  int nextState = 0;
  late HostState host;
  final live = <String, TileState>{};
  final events = <Map<String, Object>>[];
  final elements = Map<Element, String>.identity();
  String elementId(Element element) => elements.putIfAbsent(element, () => 'E${elements.length + 1}');
}

class Host extends StatefulWidget {
  const Host({required this.mode, required this.recorder, super.key});
  final MoveMode mode;
  final Recorder recorder;
  @override
  State<Host> createState() => HostState();
}

class HostState extends State<Host> {
  // buildの度に作り直さない。全段階でこの同じKeyオブジェクトを使う。
  final movingKey = GlobalKey<TileState>(debugLabel: 'one-moving-item');
  final localKey = const ValueKey<String>('one-moving-item');
  String? location = 'left';
  bool get usesGlobalKey => widget.mode != MoveMode.valueSameFrame;
  Key get childKey => usesGlobalKey ? movingKey : localKey;
  @override
  void initState() { super.initState(); widget.recorder.host = this; }
  void increment() => widget.recorder.live.values.single.increment();
  void transition() => setState(() {
    location = widget.mode == MoveMode.globalGap ? null : 'right';
  });
  void addAtRight() { if (location != 'right') setState(() { location = 'right'; }); }

  @override
  Widget build(BuildContext context) => Directionality(
    textDirection: TextDirection.ltr,
    child: Align(alignment: Alignment.topLeft, child: SizedBox(
      width: 400, height: 160,
      child: Row(children: [
        for (final slot in ['left', 'right']) Expanded(child: Slot(
          key: ValueKey<String>('parent-$slot'), id: slot,
          child: location == slot ? Tile(key: childKey, recorder: widget.recorder) : null,
        )),
      ]),
    )),
  );
}

class Slot extends StatelessWidget {
  const Slot({required this.id, this.child, super.key});
  final String id;
  final Widget? child;
  @override
  Widget build(BuildContext context) => Column(children: [
    Text('親 $id', style: const TextStyle(fontSize: 14, color: Color(0xFF173C36))),
    if (child != null) child!,
  ]);
}

class Tile extends StatefulWidget {
  const Tile({required this.recorder, super.key});
  final Recorder recorder;
  @override
  State<Tile> createState() => TileState();
}

class TileState extends State<Tile> {
  late final Recorder recorder;
  late final String stateId;
  int count = 0;
  String get label => '項目 A / State $stateId / 回数 $count';
  void record(String event) => recorder.events.add({
    'event': event, 'stateId': stateId, 'count': count,
  });
  @override
  void initState() {
    super.initState(); recorder = widget.recorder;
    stateId = 'S${++recorder.nextState}'; recorder.live[stateId] = this;
    record('initState');
  }
  void increment() => setState(() { count++; record('increment'); });
  @override
  void deactivate() { record('deactivate'); super.deactivate(); }
  @override
  void activate() { super.activate(); record('activate'); }
  @override
  void didUpdateWidget(Tile oldWidget) { super.didUpdateWidget(oldWidget); record('didUpdateWidget'); }
  @override
  void dispose() { record('dispose'); recorder.live.remove(stateId); super.dispose(); }
  @override
  Widget build(BuildContext context) => SizedBox(width: 190, height: 80,
    child: ColoredBox(color: const Color(0xFFE8F5F0), child: Center(child: Text(label,
      style: const TextStyle(fontSize: 13, color: Color(0xFF173C36))))));
}
