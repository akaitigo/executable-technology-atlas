// 未コンパイル・未実行。将来の実Flutter engine観測用。
// 予測不一致を保存し、可能な限り後続段階・もう一方の条件も観測する。
import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/rendering.dart' show RenderBox;
import 'package:flutter/widgets.dart';
import 'package:listview_state_probe/listview_probe.dart';

final report = <String, Object?>{
  'kind': 'actual_flutter_engine_widget_probe',
  'executionStatus': 'running', 'passed': false,
  'standardFlutterTestHarness': false, 'visualQaPerformed': false,
  'inputMethod': 'programmatic State methods and ScrollController.jumpTo; no pointer input',
  'cases': <Map<String, Object?>>[], 'flutterErrors': <String>[],
};
final cases = report['cases']! as List<Map<String, Object?>>;
final flutterErrors = report['flutterErrors']! as List<String>;

void save() {
  final output = Platform.environment['PROBE_OUTPUT'];
  if (output == null) throw StateError('PROBE_OUTPUT is required');
  File(output).writeAsStringSync('${const JsonEncoder.withIndent('  ').convert(report)}\n');
}

Future<void> frames() async {
  await WidgetsBinding.instance.endOfFrame;
  await WidgetsBinding.instance.endOfFrame;
}

List<Map<String, Object?>> snapshot(ProbeHostState host) {
  final tiles = host.tilesInTreeOrder();
  final rows = <Map<String, Object?>>[];
  for (var i = 0; i < tiles.length; i++) {
    final tile = tiles[i];
    final texts = <String>[];
    void visit(Element element) {
      if (element.widget is Text) texts.add((element.widget as Text).data ?? '');
      element.visitChildren(visit);
    }
    tile.context.visitChildElements(visit);
    final render = tile.context.findRenderObject();
    rows.add({
      'treeOrder': i, 'index': host.order.indexOf(tile.widget.itemId),
      'itemId': tile.widget.itemId, 'stateId': tile.stateId,
      'mountedFor': tile.mountedFor, 'count': tile.count,
      'texts': texts, 'expectedTextFromState': tile.label,
      if (render is RenderBox && render.hasSize)
        'renderBox': {'top': render.localToGlobal(Offset.zero).dy,
          'width': render.size.width, 'height': render.size.height},
    });
  }
  // 元の探索順もtreeOrderに保存し、固定表との照合は現在の項目indexで行う。
  rows.sort((a, b) => (a['index']! as int).compareTo(b['index']! as int));
  return rows;
}

void compare(Map<String, dynamic> expected, Map<String, Object?> stage,
    Map<String, String> symbols) {
  final differences = stage['differences']! as List<String>;
  void equal(Object? got, Object? want, String label) {
    if (jsonEncode(got) != jsonEncode(want)) {
      differences.add('$label: expected=${jsonEncode(want)}, actual=${jsonEncode(got)}');
    }
  }
  final rows = stage['rows']! as List<Map<String, Object?>>;
  final wanted = expected['rows'] as List<dynamic>;
  final created = (expected['created'] as List<dynamic>).cast<String>();
  equal(rows.length, wanted.length, 'mounted row count (unexecuted prediction)');
  for (final raw in wanted) {
    final row = raw as List<dynamic>;
    final item = row[0] as String;
    final symbol = row[1] as String;
    final found = rows.where((entry) => entry['itemId'] == item).toList();
    if (found.length != 1) {
      differences.add('item $item: expected exactly one mounted row, actual=${found.length}');
      continue;
    }
    final got = found.single;
    final id = got['stateId']! as String;
    if (created.contains(symbol)) {
      if (symbols.containsKey(symbol) || symbols.containsValue(id)) {
        differences.add('$symbol expected a fresh State but observed $id');
      } else {
        symbols[symbol] = id;
      }
    }
    equal(id, symbols[symbol], '$item State identity $symbol');
    equal(got['mountedFor'], row[2], '$item mountedFor');
    equal(got['count'], row[3], '$item count');
    equal(got['texts'], [got['expectedTextFromState']], '$item Element Text');
  }
  equal(rows.map((row) => row['itemId']).toList(),
    wanted.map((row) => row[0]).toList(), 'logical order');
  equal(stage['offset'], (expected['offset'] as num).toDouble(), 'scroll offset');
  final events = stage['events']! as List<Map<String, Object>>;
  for (final pair in [('initState', 'created'), ('dispose', 'disposed')]) {
    final got = events.where((event) => event['event'] == pair.$1)
      .map((event) => event['stateId']! as String).toList()..sort();
    final wantedIds = (expected[pair.$2] as List<dynamic>)
      .map((symbol) => symbols[symbol] ?? 'UNRESOLVED:$symbol').toList()..sort();
    equal(got, wantedIds, '${pair.$1} set; event ordering is not asserted');
  }
  if (expected.containsKey('predictedBuiltIndexSet')) {
    final indices = (stage['builderCalls']! as List<Map<String, Object>>)
      .map((call) => call['index']! as int).toSet().toList()..sort();
    equal(indices, expected['predictedBuiltIndexSet'], 'unique built indices (prediction)');
  }
  final mountedIds = rows.map((row) => row['stateId']! as String).toList()..sort();
  equal(stage['liveStateIds'], mountedIds, 'registry versus actual Element traversal');
}

Future<void> runProbe() async {
  WidgetsFlutterBinding.ensureInitialized();
  FlutterError.onError = (details) { flutterErrors.add(details.toString()); save(); };
  final fixed = jsonDecode(File(Platform.environment['PROBE_EXPECTATIONS']!).readAsStringSync())
    as Map<String, dynamic>;
  for (final rawCase in fixed['cases'] as List<dynamic>) {
    final fixedCase = rawCase as Map<String, dynamic>;
    final mode = LookupMode.values.byName(fixedCase['id'] as String);
    final recorder = ProbeRecorder();
    final stages = <Map<String, Object?>>[];
    final symbols = <String, String>{};
    final observed = <String, Object?>{
      'id': mode.name, 'passed': false, 'stages': stages, 'symbols': symbols,
      'allLifecycleEvents': recorder.events, 'allBuilderCalls': recorder.builds,
      'allLookupCalls': recorder.lookups,
    };
    cases.add(observed); save();
    for (final rawPhase in fixedCase['phases'] as List<dynamic>) {
      final expected = rawPhase as Map<String, dynamic>;
      final phase = expected['id'] as String;
      final differences = <String>[];
      final stage = <String, Object?>{
        'phase': phase, 'expected': expected, 'differences': differences,
        'passed': false,
      };
      stages.add(stage);
      final eventStart = recorder.events.length;
      final buildStart = recorder.builds.length;
      final lookupStart = recorder.lookups.length;
      try {
        switch (phase) {
          case 'initial':
            runApp(ProbeHost(key: ValueKey(mode.name), mode: mode, recorder: recorder));
          case 'prepared':
            recorder.host.increment('A');
            recorder.host.increment('B'); recorder.host.increment('B');
          case 'reordered': recorder.host.swapFirstTwo();
          case 'far': recorder.host.controller.jumpTo(640);
          case 'returned': recorder.host.controller.jumpTo(0);
          default: throw StateError('unknown phase $phase');
        }
        await frames();
        final host = recorder.host;
        final live = recorder.live.keys.toList()..sort();
        stage.addAll({
          'rows': snapshot(host), 'offset': host.controller.offset,
          'order': List<String>.of(host.order), 'liveStateIds': live,
          'events': recorder.events.sublist(eventStart),
          'builderCalls': recorder.builds.sublist(buildStart),
          'lookupCalls': recorder.lookups.sublist(lookupStart),
        });
        save(); // 比較に先立ち、予測と独立した実測を保存する。
        compare(expected, stage, symbols);
        stage['passed'] = differences.isEmpty;
      } catch (error, stack) {
        stage['failure'] = error.toString(); stage['stack'] = stack.toString();
      }
      save();
    }
    final cleanupStart = recorder.events.length;
    try {
      runApp(const SizedBox.shrink()); await frames();
      observed['cleanupEvents'] = recorder.events.sublist(cleanupStart);
      observed['cleanupPassed'] = recorder.live.isEmpty;
    } catch (error) { observed['cleanupFailure'] = error.toString(); }
    observed['passed'] = stages.every((stage) => stage['passed'] == true) &&
      observed['cleanupPassed'] == true;
    save();
  }
  report['caseCount'] = cases.length;
  report['snapshotCount'] = cases.fold<int>(0,
    (count, item) => count + (item['stages']! as List).where((stage) => stage.containsKey('rows')).length);
  report['passed'] = cases.length == 2 && report['snapshotCount'] == 10 &&
    cases.every((item) => item['passed'] == true) && flutterErrors.isEmpty;
  report['executionStatus'] = 'completed'; save();
}

void main() {
  runZonedGuarded(() async {
    final timeout = Timer(const Duration(seconds: 20), () {
      report['executionStatus'] = 'timeout'; save(); exit(124);
    });
    await runProbe(); timeout.cancel();
    print('固定予測との照合: ${report['passed']}; 原票はPROBE_OUTPUTに保存');
    exit(report['passed'] == true ? 0 : 1);
  }, (error, stack) {
    report['executionStatus'] = 'failed'; report['failure'] = error.toString();
    report['stack'] = stack.toString(); save(); stderr.writeln(error); exit(1);
  });
}
