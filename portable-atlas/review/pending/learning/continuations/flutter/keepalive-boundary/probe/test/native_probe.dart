// 未実行の実Widget観測用。比較前に原票を保存し、予測不一致を捨てない。
import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/rendering.dart';
import 'package:flutter/widgets.dart';
import 'package:keepalive_boundary_probe/keepalive_probe.dart';

final report = <String, Object?>{
  'kind': 'actual_flutter_engine_widget_probe', 'executionStatus': 'running',
  'passed': false, 'standardFlutterTestHarness': false, 'visualQaPerformed': false,
  'inputMethod': 'programmatic State methods and ScrollController.jumpTo; no pointer input',
  'storageMeaning': 'cached = public SliverMultiBoxAdaptorParentData.keptAlive; layout = not cached',
  'cases': <Map<String, Object?>>[], 'flutterErrors': <String>[],
};
final cases = report['cases']! as List<Map<String, Object?>>;
final flutterErrors = report['flutterErrors']! as List<String>;

void save() => File(Platform.environment['PROBE_OUTPUT']!).writeAsStringSync(
  '${const JsonEncoder.withIndent('  ').convert(report)}\n');

Future<void> frames() async {
  await WidgetsBinding.instance.endOfFrame;
  await WidgetsBinding.instance.endOfFrame;
}

List<Map<String, Object?>> snapshot(HostState host) {
  final result = <Map<String, Object?>>[];
  for (final tile in host.tilesInElementTree()) {
    RenderObject? render = tile.context.findRenderObject();
    while (render != null && render.parentData is! SliverMultiBoxAdaptorParentData) {
      render = render.parent;
    }
    if (render == null) throw StateError('Sliver parent data not found for ${tile.widget.itemId}');
    final parent = render.parentData! as SliverMultiBoxAdaptorParentData;
    final texts = <String>[];
    void visit(Element element) {
      if (element.widget is Text) texts.add((element.widget as Text).data ?? '');
      element.visitChildren(visit);
    }
    tile.context.visitChildElements(visit);
    result.add({
      'itemId': tile.widget.itemId, 'stateId': tile.stateId, 'mountedFor': tile.mountedFor,
      'count': tile.count, 'mounted': tile.mounted, 'wantKeepAlive': tile.keepRequested,
      'keepAlive': parent.keepAlive, 'keptAlive': parent.keptAlive,
      'storage': parent.keptAlive ? 'cached' : 'layout', 'renderIndex': parent.index,
      'layoutOffset': parent.layoutOffset, 'texts': texts,
    });
  }
  result.sort((a, b) => (a['renderIndex']! as int).compareTo(b['renderIndex']! as int));
  return result;
}

void compare(Map<String, dynamic> expected, Map<String, Object?> stage,
    Map<String, String> symbols, bool requested) {
  final differences = stage['differences']! as List<String>;
  void equal(Object? got, Object? wanted, String name) {
    if (jsonEncode(got) != jsonEncode(wanted)) {
      differences.add('$name: expected=${jsonEncode(wanted)} actual=${jsonEncode(got)}');
    }
  }
  final rows = stage['rows']! as List<Map<String, Object?>>;
  final wanted = expected['rows'] as List<dynamic>;
  final fresh = (expected['created'] as List<dynamic>).cast<String>();
  equal(rows.length, wanted.length, 'all mounted States, including cached');
  for (final entry in wanted) {
    final row = entry as List<dynamic>;
    final matches = rows.where((r) => r['itemId'] == row[0]).toList();
    if (matches.length != 1) { differences.add('${row[0]}: expected one State, actual=${matches.length}'); continue; }
    final got = matches.single;
    final symbol = row[1] as String, stateId = got['stateId']! as String;
    if (fresh.contains(symbol)) {
      if (symbols.containsKey(symbol) || symbols.containsValue(stateId)) {
        differences.add('$symbol was expected to be fresh but found $stateId');
      } else { symbols[symbol] = stateId; }
    }
    equal(stateId, symbols[symbol], '${row[0]} State identity');
    equal(got['count'], row[2], '${row[0]} counter');
    equal(got['storage'], row[3], '${row[0]} cached/layout');
    equal(got['mountedFor'], row[0], '${row[0]} mountedFor');
    equal(got['mounted'], true, '${row[0]} mounted');
    equal(got['wantKeepAlive'], requested, '${row[0]} requested');
    equal(got['keepAlive'], requested, '${row[0]} parent data request');
    equal(got['texts'], ['項目 ${got['itemId']} / State $stateId / 回数 ${got['count']}'], '${row[0]} Element Text');
  }
  equal(rows.map((r) => r['itemId']).toList(), wanted.map((r) => r[0]).toList(), 'mounted item order');
  equal(rows.where((r) => r['storage'] == 'layout').map((r) => r['itemId']).toList(),
    expected['layoutItems'], 'layout items versus cached items');
  equal(stage['offset'], (expected['offset'] as num).toDouble(), 'scroll offset');
  final live = rows.map((r) => r['stateId']! as String).toList()..sort();
  equal(stage['registryStateIds'], live, 'registry versus actual Element tree');
  final events = stage['events']! as List<Map<String, Object>>;
  for (final pair in [('initState', 'created'), ('dispose', 'disposed')]) {
    final got = events.where((event) => event['event'] == pair.$1)
      .map((event) => event['stateId']! as String).toList()..sort();
    final ids = (expected[pair.$2] as List<dynamic>)
      .map((symbol) => symbols[symbol] ?? 'UNRESOLVED:$symbol').toList()..sort();
    equal(got, ids, '${pair.$1} set, not callback ordering');
  }
}

Future<void> runProbe() async {
  WidgetsFlutterBinding.ensureInitialized();
  FlutterError.onError = (details) { flutterErrors.add(details.toString()); save(); };
  final fixed = jsonDecode(File(Platform.environment['PROBE_EXPECTATIONS']!).readAsStringSync())
    as Map<String, dynamic>;
  for (final rawCase in fixed['cases'] as List<dynamic>) {
    final expectedCase = rawCase as Map<String, dynamic>;
    final mode = KeepMode.values.byName(expectedCase['id'] as String);
    final recorder = Recorder();
    final symbols = <String, String>{};
    final stages = <Map<String, Object?>>[];
    final observed = <String, Object?>{
      'id': mode.name, 'passed': false, 'stages': stages, 'symbols': symbols,
      'allLifecycleEvents': recorder.events, 'allBuilderCalls': recorder.builderCalls,
    };
    cases.add(observed); save();
    for (final rawPhase in expectedCase['phases'] as List<dynamic>) {
      final expected = rawPhase as Map<String, dynamic>;
      final phase = expected['id'] as String;
      final stage = <String, Object?>{
        'phase': phase, 'expected': expected, 'differences': <String>[], 'passed': false,
      };
      stages.add(stage);
      final eventStart = recorder.events.length, builderStart = recorder.builderCalls.length;
      try {
        switch (phase) {
          case 'initial': runApp(Host(key: ValueKey(mode.name), mode: mode, recorder: recorder));
          case 'prepared': recorder.host.increment('A'); recorder.host.increment('B'); recorder.host.increment('B');
          case 'far': recorder.host.controller.jumpTo(640);
          case 'returned': recorder.host.controller.jumpTo(0);
          default: throw StateError('unknown phase $phase');
        }
        await frames();
        final ids = recorder.live.keys.toList()..sort();
        stage.addAll({'rows': snapshot(recorder.host), 'offset': recorder.host.controller.offset,
          'registryStateIds': ids, 'events': recorder.events.sublist(eventStart),
          'builderCalls': recorder.builderCalls.sublist(builderStart)});
        save();
        compare(expected, stage, symbols, expectedCase['wantKeepAlive'] as bool);
        stage['passed'] = (stage['differences']! as List).isEmpty;
      } catch (error, stack) { stage['failure'] = error.toString(); stage['stack'] = stack.toString(); }
      save();
    }
    final cleanupStart = recorder.events.length;
    try {
      runApp(const SizedBox.shrink()); await frames();
      observed['cleanupEvents'] = recorder.events.sublist(cleanupStart);
      observed['cleanupPassed'] = recorder.live.isEmpty;
    } catch (error) { observed['cleanupFailure'] = error.toString(); }
    observed['passed'] = stages.every((s) => s['passed'] == true) && observed['cleanupPassed'] == true;
    save();
  }
  report['caseCount'] = cases.length;
  report['snapshotCount'] = cases.fold<int>(0,
    (sum, c) => sum + (c['stages']! as List).where((s) => s.containsKey('rows')).length);
  report['passed'] = cases.length == 2 && report['snapshotCount'] == 8 &&
    cases.every((c) => c['passed'] == true) && flutterErrors.isEmpty;
  report['executionStatus'] = 'completed'; save();
}

void main() {
  runZonedGuarded(() async {
    final timeout = Timer(const Duration(seconds: 20), () {
      report['executionStatus'] = 'timeout'; save(); exit(124);
    });
    await runProbe(); timeout.cancel();
    print('keep-alive固定予測との照合: ${report['passed']}');
    exit(report['passed'] == true ? 0 : 1);
  }, (error, stack) {
    report['executionStatus'] = 'failed'; report['failure'] = error.toString();
    report['stack'] = stack.toString(); save(); stderr.writeln(error); exit(1);
  });
}
