// 原票を固定予測の比較前に保存する。失敗・予測不一致も残す。
import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/widgets.dart';
import 'package:globalkey_reparent_probe/reparent_probe.dart';

final report = <String, Object?>{
  'kind': 'actual_flutter_engine_widget_probe', 'executionStatus': 'running',
  'passed': false, 'standardFlutterTestHarness': false, 'visualQaPerformed': false,
  'inputMethod': 'programmatic State methods; no pointer input',
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

Map<String, Object?> snapshot(Recorder recorder) {
  final rows = <Map<String, Object?>>[], parents = <Map<String, Object?>>[];
  void visit(Element element) {
    if (element.widget is Slot) {
      parents.add({'slot': (element.widget as Slot).id, 'elementId': recorder.elementId(element)});
    }
    if (element is StatefulElement && element.state is TileState) {
      final tile = element.state as TileState;
      Element? slotElement, directParent;
      element.visitAncestorElements((ancestor) {
        directParent ??= ancestor;
        if (ancestor.widget is Slot) { slotElement = ancestor; return false; }
        return true;
      });
      if (slotElement == null || directParent == null) throw StateError('親Elementが見つかりません');
      final texts = <String>[];
      void textVisit(Element child) {
        if (child.widget is Text) texts.add((child.widget as Text).data ?? '');
        child.visitChildren(textVisit);
      }
      element.visitChildren(textVisit);
      rows.add({'itemId': 'A', 'stateId': tile.stateId, 'count': tile.count,
        'mounted': tile.mounted, 'slot': (slotElement!.widget as Slot).id,
        'elementId': recorder.elementId(element),
        'parentElementId': recorder.elementId(directParent!),
        'slotElementId': recorder.elementId(slotElement!),
        'keyKind': recorder.host.usesGlobalKey ? 'GlobalKey' : 'ValueKey',
        'sameKeyObject': identical(tile.widget.key, recorder.host.childKey), 'texts': texts});
    }
    element.visitChildren(visit);
  }
  recorder.host.context.visitChildElements(visit);
  return {'rows': rows, 'parents': parents,
    'registryStateIds': recorder.live.keys.toList()..sort(),
    'globalCurrentStateId': recorder.host.usesGlobalKey ? recorder.host.movingKey.currentState?.stateId : null,
    'hostLocation': recorder.host.location};
}

void compare(Map<String, dynamic> expected, Map<String, Object?> stage,
    Map<String, String> symbols, Map<String, String> elementSymbols, bool global) {
  final differences = stage['differences']! as List<String>;
  void equal(Object? got, Object? wanted, String name) {
    if (jsonEncode(got) != jsonEncode(wanted)) differences.add('$name: expected=${jsonEncode(wanted)} actual=${jsonEncode(got)}');
  }
  final rows = stage['rows']! as List<Map<String, Object?>>;
  final wanted = expected['rows'] as List<dynamic>;
  final fresh = (expected['created'] as List<dynamic>).cast<String>();
  equal(rows.length, wanted.length, 'active Tile count');
  for (var i = 0; i < wanted.length && i < rows.length; i++) {
    final w = wanted[i] as List<dynamic>, row = rows[i];
    final symbol = w[0] as String, id = row['stateId']! as String;
    final eid = row['elementId']! as String;
    if (fresh.contains(symbol)) {
      if (symbols.containsKey(symbol) || symbols.containsValue(id) || elementSymbols.containsValue(eid)) {
        differences.add('$symbol must be a new State and Element');
      } else { symbols[symbol] = id; elementSymbols[symbol] = eid; }
    }
    equal(id, symbols[symbol], 'State identity');
    equal(eid, elementSymbols[symbol], 'Element identity');
    equal(row['count'], w[1], 'counter'); equal(row['slot'], w[2], 'parent slot');
    equal(row['mounted'], true, 'mounted'); equal(row['sameKeyObject'], true, 'same Key object');
    equal(row['keyKind'], global ? 'GlobalKey' : 'ValueKey', 'Key kind');
    equal(row['texts'], ['項目 A / State $id / 回数 ${row['count']}'], 'Element Text');
  }
  final ids = rows.map((r) => r['stateId']).toList()..sort((a, b) => (a! as String).compareTo(b! as String));
  equal(stage['registryStateIds'], ids, 'registry versus actual Element tree');
  equal(stage['hostLocation'], expected['location'], 'host location');
  equal(stage['globalCurrentStateId'], global && rows.isNotEmpty ? rows.single['stateId'] : null, 'GlobalKey currentState');
  final events = stage['events']! as List<Map<String, Object>>;
  for (final pair in [('initState', 'created'), ('dispose', 'disposed'), ('deactivate', 'deactivated'), ('activate', 'activated')]) {
    final got = events.where((e) => e['event'] == pair.$1).map((e) => e['stateId']! as String).toList()..sort();
    final wantedIds = (expected[pair.$2] as List<dynamic>).map((s) => symbols[s] ?? 'UNRESOLVED:$s').toList()..sort();
    equal(got, wantedIds, '${pair.$1} set; no total callback ordering assumption');
  }
}

Future<void> runProbe() async {
  WidgetsFlutterBinding.ensureInitialized();
  FlutterError.onError = (details) { flutterErrors.add(details.toString()); save(); };
  final fixed = jsonDecode(File(Platform.environment['PROBE_EXPECTATIONS']!).readAsStringSync()) as Map<String, dynamic>;
  for (final rawCase in fixed['cases'] as List<dynamic>) {
    final expectedCase = rawCase as Map<String, dynamic>;
    final mode = MoveMode.values.byName(expectedCase['id'] as String);
    final recorder = Recorder(), symbols = <String, String>{}, elementSymbols = <String, String>{};
    final stages = <Map<String, Object?>>[];
    final observed = <String, Object?>{'id': mode.name, 'passed': false, 'stages': stages,
      'symbols': symbols, 'elementSymbols': elementSymbols, 'allLifecycleEvents': recorder.events};
    cases.add(observed); save();
    for (final rawPhase in expectedCase['phases'] as List<dynamic>) {
      final expected = rawPhase as Map<String, dynamic>, phase = expected['id'] as String;
      final stage = <String, Object?>{'phase': phase, 'expected': expected, 'differences': <String>[], 'passed': false};
      stages.add(stage); final eventStart = recorder.events.length;
      try {
        switch (phase) {
          case 'initial': runApp(Host(key: ValueKey(mode.name), mode: mode, recorder: recorder));
          case 'prepared': recorder.host.increment();
          case 'transition': recorder.host.transition();
          case 'atRight': recorder.host.addAtRight();
          default: throw StateError('unknown phase $phase');
        }
        // transitionの操作を終えたframeのfinalizeTreeを通過してから次の操作へ進む。
        await frames(); stage.addAll(snapshot(recorder));
        stage['events'] = recorder.events.sublist(eventStart); save();
        compare(expected, stage, symbols, elementSymbols, recorder.host.usesGlobalKey);
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
    observed['passed'] = stages.every((s) => s['passed'] == true) && observed['cleanupPassed'] == true; save();
  }
  report['caseCount'] = cases.length;
  report['snapshotCount'] = cases.fold<int>(0, (sum, c) => sum + (c['stages']! as List).where((s) => s.containsKey('rows')).length);
  report['passed'] = cases.length == 3 && report['snapshotCount'] == 12 && cases.every((c) => c['passed'] == true) && flutterErrors.isEmpty;
  report['executionStatus'] = 'completed'; save();
}

void main() {
  runZonedGuarded(() async {
    final timeout = Timer(const Duration(seconds: 20), () { report['executionStatus'] = 'timeout'; save(); exit(124); });
    await runProbe(); timeout.cancel(); print('GlobalKey fixed prediction comparison: ${report['passed']}');
    exit(report['passed'] == true ? 0 : 1);
  }, (error, stack) {
    report['executionStatus'] = 'failed'; report['failure'] = error.toString(); report['stack'] = stack.toString();
    save(); stderr.writeln(error); exit(1);
  });
}
