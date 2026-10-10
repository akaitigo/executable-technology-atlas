#!/usr/bin/env python3
"""既定は読取のみの実行計画。--execute は資源条件・実行枠確保後の将来用。"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from urllib.parse import unquote, urlparse


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(sdk, cached, lesson):
    version = json.loads((sdk / 'bin/cache/flutter.version.json').read_text())
    required = {
        'frameworkVersion': '3.47.1',
        'frameworkRevision': '6655482ec06e547f90abf8ae7590466f4415978d',
        'dartSdkVersion': '3.13.1',
    }
    for field, value in required.items():
        if version.get(field) != value:
            raise ValueError(f'固定SDK不一致: {field}')
    engine = sdk / 'bin/cache/artifacts/engine/darwin-x64'
    for path in (engine / 'flutter_tester', engine / 'frontend_server_aot.dart.snapshot',
                 engine / 'icudtl.dat', sdk / 'bin/cache/dart-sdk/bin/dartaotruntime'):
        if not path.is_file():
            raise ValueError(f'既存artifact不足: {path.name}')
    fixed = json.loads((lesson / 'expectations.json').read_text())
    if fixed['fixture'] != {
        'items': list('ABCDEFGHIJKL'), 'viewportWidth': 320, 'viewportHeight': 160,
        'itemExtent': 80, 'cachePixels': 0, 'automaticKeepAlive': True,
        'pageStorageScrollOffset': False,
    }:
        raise ValueError('予測表とコードのfixtureを再照合してください')
    config = json.loads(cached.read_text())
    packages = []
    for source in config['packages']:
        if source['name'] in ('widget_state_lifecycle_lesson', 'keepalive_boundary_probe'):
            continue
        item = dict(source)
        uri = item['rootUri']
        parsed = urlparse(uri)
        if parsed.scheme not in ('', 'file'):
            raise ValueError('ローカルpackage cacheのみ使用可能')
        package_root = (Path(unquote(parsed.path)) if parsed.scheme == 'file'
                        else cached.parent / unquote(uri)).resolve()
        if not package_root.is_dir():
            raise ValueError(f'package cache不足: {item["name"]}')
        item['rootUri'] = package_root.as_uri()
        packages.append(item)
    flutter = [item for item in packages if item['name'] == 'flutter']
    if len(flutter) != 1 or flutter[0]['rootUri'] != (sdk / 'packages/flutter').as_uri():
        raise ValueError('package configのFlutter参照が固定SDKと異なります')
    packages.append({'name': 'keepalive_boundary_probe', 'rootUri': (lesson / 'probe').as_uri(),
                     'packageUri': 'lib/', 'languageVersion': '3.13'})
    return version, packages


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--cached-package-config', type=Path, required=True)
    parser.add_argument('--execute', action='store_true', help='資源条件を確認済みの実行枠でのみ指定')
    parser.add_argument('--attempt', type=int, default=1)
    args = parser.parse_args()
    lesson = Path(__file__).resolve().parents[1]
    probe = lesson / 'probe'
    sdk, cached = args.sdk.resolve(), args.cached_package_config.resolve()
    version, packages = validate(sdk, cached, lesson)
    if not args.execute:
        print(json.dumps({'mode': 'read_only_plan', 'runtimeExecuted': False,
            'writes': False, 'sdkVersion': version['frameworkVersion'],
            'plannedCases': 2, 'plannedSnapshots': 8,
            'futureLimitsSeconds': {'compile': 45, 'tester': 25, 'probeInternal': 20},
            'requires': 'その時点の全体資源確認と担当間の実行枠調整。'},
            ensure_ascii=False, indent=2))
        return 0
    if args.attempt < 1:
        parser.error('--attempt は1以上')
    output = probe / 'observations' / f'attempt-{args.attempt:02d}'
    output.mkdir(parents=True, exist_ok=False)
    local = output / 'local'
    for name in ('config', 'tmp'):
        (local / name).mkdir(parents=True)
    receipt = {
        'startedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'passed': False, 'attempt': args.attempt, 'sdkMetadata': version,
        'sdkMetadataNote': '既存metadata照合。配布物全体の再取得・全体hashではない。',
        'standardFlutterTestHarness': False, 'visualQaPerformed': False,
        'pubGetRun': False, 'sdkWriteRequested': False, 'steps': [],
        'maxConcurrentCommands': 1, 'loadBefore': os.getloadavg(),
        'resourceGateAutomaticallyEvaluated': False,
        'priorityFailurePolicy': '子プロセスのos.nice(10)成功前はexecしない。失敗時は中止。',
    }

    def save():
        (output / 'run.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')

    save()
    try:
        package_config = local / 'package_config.json'
        package_config.write_text(json.dumps({'configVersion': 2, 'packages': packages}, indent=2) + '\n')
        inputs = {name: lesson / name for name in (
            'expectations.json', 'probe/pubspec.yaml', 'probe/lib/keepalive_probe.dart',
            'probe/test/native_probe.dart', 'probe/run_probe.py')}
        receipt['inputSha256'] = {name: digest(path) for name, path in inputs.items()}
        for name, path in inputs.items():
            target = output / 'inputs' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        save()
        engine = sdk / 'bin/cache/artifacts/engine/darwin-x64'
        kernel = output / 'probe.dill'
        env = dict(os.environ)
        env.update({'DART_SUPPRESS_ANALYTICS': 'true', 'FLUTTER_SUPPRESS_ANALYTICS': 'true',
            'XDG_CONFIG_HOME': str(local / 'config'), 'TMPDIR': str(local / 'tmp'),
            'PROBE_EXPECTATIONS': str(output / 'inputs/expectations.json'),
            'PROBE_OUTPUT': str(output / 'actual.json')})
        commands = [
            ('compile', 45, [str(sdk / 'bin/cache/dart-sdk/bin/dartaotruntime'),
                str(engine / 'frontend_server_aot.dart.snapshot'), '--sdk-root',
                str(sdk / 'bin/cache/artifacts/engine/common/flutter_patched_sdk'),
                '--target=flutter', '--no-print-incremental-dependencies',
                '--packages', str(package_config), '--output-dill', str(kernel),
                '--verbosity=error', str(probe / 'test/native_probe.dart')]),
            ('widgetProbe', 25, [str(engine / 'flutter_tester'), '--disable-vm-service',
                '--enable-checked-mode', '--verify-entry-points', '--enable-software-rendering',
                '--skia-deterministic-rendering', '--non-interactive', '--use-test-fonts',
                '--disable-asset-fonts', '--icu-data-file-path=' + str(engine / 'icudtl.dat'),
                '--packages=' + str(package_config), str(kernel)]),
        ]
        for name, timeout, command in commands:
            step = {'name': name, 'status': 'starting', 'timeoutSeconds': timeout,
                    'command': [part.replace(str(sdk), '${SDK}').replace(str(lesson), '${LESSON}')
                                for part in command]}
            receipt['steps'].append(step); save()
            started = time.monotonic()
            priority_file = output / f'{name}.priority.json'

            def lower_priority():
                effective = os.nice(10)
                if effective < 10:
                    raise RuntimeError('優先度を下げられませんでした')
                priority_file.write_text(json.dumps({'pid': os.getpid(),
                    'effectiveNice': os.getpriority(os.PRIO_PROCESS, 0)}) + '\n')

            with (output / f'{name}.stdout.txt').open('wb') as stdout, \
                    (output / f'{name}.stderr.txt').open('wb') as stderr:
                result = subprocess.run(command, cwd=probe, env=env, stdout=stdout, stderr=stderr,
                    preexec_fn=lower_priority, timeout=timeout)
            step.update(status='completed', exitCode=result.returncode,
                        elapsedSeconds=round(time.monotonic() - started, 3),
                        priority=json.loads(priority_file.read_text()))
            save()
            if result.returncode != 0:
                raise RuntimeError(f'{name} exit {result.returncode}; 原票・差分は削除しません')
        actual = json.loads((output / 'actual.json').read_text())
        if not actual['passed'] or actual['caseCount'] != 2 or actual['snapshotCount'] != 8:
            raise RuntimeError('全条件・全段階の照合が成立しませんでした')
        if any(digest(path) != receipt['inputSha256'][name] for name, path in inputs.items()):
            raise RuntimeError('実行中に入力が変化しました')
        receipt['passed'] = True
    except Exception as error:
        receipt['failure'] = f'{type(error).__name__}: {error}'
        if receipt['steps'] and receipt['steps'][-1]['status'] == 'starting':
            receipt['steps'][-1]['status'] = 'failed_before_completion'
    finally:
        actual_path = output / 'actual.json'
        if actual_path.is_file():
            receipt['actualSha256'] = digest(actual_path)
        receipt['finishedAt'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        receipt['loadAfter'] = os.getloadavg(); save()
    print(json.dumps({'passed': receipt['passed'], 'failure': receipt.get('failure'),
                     'output': str(output)}, ensure_ascii=False))
    return 0 if receipt['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
