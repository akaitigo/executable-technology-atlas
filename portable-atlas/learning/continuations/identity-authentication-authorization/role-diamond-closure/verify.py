"""Read saved JSON and manual expectations; never import the producer/model."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
RESULT_FIELDS = ['reachable_set', 'reachable_order', 'direct_permissions', 'inherited_permissions',
                 'overlap_permissions', 'effective_permissions', 'permission_sources']


def inspect(raw):
    expected = json.loads((ROOT / 'expected.json').read_text())
    fixture = json.loads((ROOT / 'inputs/cases.json').read_text())
    checks = []
    def ck(label, passed):
        checks.append({'label': label, 'passed': bool(passed)})
    ck('complete', raw.get('complete') is True and raw.get('errors') == [])
    ck('case-order', [r['id'] for r in raw['results']] == [c['id'] for c in expected['cases']])
    ck('started-five', raw['model_cases_started'] == 5)
    ck('fixture-binding', raw['fixture'] == fixture)
    ck('source-binding', raw['source_sha256'] == {n: sha(ROOT / n) for n in ['role_model.py', 'run.py', 'inputs/cases.json']} and raw['source_unchanged'] is True)
    ck('actual-nice', raw['execution']['nice_before'] >= 10 and raw['execution']['nice_after'] >= 10)
    for r, e in zip(raw['results'], expected['cases']):
        tag = e['id']
        for key in ['graph', 'requested_role', 'mode', 'status', 'reason'] + RESULT_FIELDS:
            ck(tag + ':' + key, r[key] == e[key])
        ck(tag + ':diagnostic', r['diagnostic'] == e['diagnostic'])
        ck(tag + ':event-count', len(r['events']) == len(e['events']))
        for i, (actual, hand) in enumerate(zip(r['events'], e['events'])):
            for key in ['index', 'action', 'role', 'target', 'active', 'visited_order', 'completed_order', 'cycle_path', 'reported_path']:
                ck(tag + ':event' + str(i) + ':' + key, actual[key] == hand[key])
        classification = 'intentional-false-positive' if e['mode'] == 'visited-only-fault' else 'resolved' if e['status'] == 'accepted' else 'expected-rejection'
        ck(tag + ':classification', r['classification'] == classification)
        graph = fixture['graphs'][r['graph']]
        if r['status'] == 'accepted':
            ck(tag + ':no-active-after-success', r['diagnostic']['active_at_stop'] == [])
            ck(tag + ':closure-no-duplicates', r['reachable_set'] == sorted(set(r['reachable_order'])))
            ck(tag + ':permission-set-algebra', r['effective_permissions'] == sorted(set(r['direct_permissions']) | set(r['inherited_permissions'])) and r['overlap_permissions'] == sorted(set(r['direct_permissions']) & set(r['inherited_permissions'])))
            ck(tag + ':source-role-sets', all(roles == sorted(set(roles)) and all(role in r['reachable_set'] and permission in fixture['permissions'][role] for role in roles) for permission, roles in r['permission_sources'].items()))
        else:
            ck(tag + ':no-partial-permission-publication', all(r[key] is None for key in RESULT_FIELDS))
        if r['reason'] == 'active-cycle':
            path = r['diagnostic']['cycle_path']
            ck(tag + ':cycle-edges', path is not None and len(path) >= 2 and path[0] == path[-1] and all(b in graph[a] for a, b in zip(path, path[1:])))
        if r['reason'] == 'visited-as-cycle':
            ck(tag + ':fault-not-true-cycle', r['diagnostic']['cycle_path'] is None and r['diagnostic']['reported_path'][0] != r['diagnostic']['reported_path'][-1] and r['events'][-1]['role'] not in r['diagnostic']['active_at_stop'])
    return checks


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('raw', type=Path); args = ap.parse_args()
    raw = json.loads(args.raw.read_text()); checks = inspect(raw); mutations = []
    def item(r, name):
        return next(c for c in r['results'] if c['id'] == name)
    def mutate(name, edit, required):
        altered = copy.deepcopy(raw); edit(altered)
        failed = [c['label'] for c in inspect(altered) if not c['passed']]
        mutations.append({'name': name, 'required_label': required, 'failed_labels': failed, 'passed': required in failed})
    mutate('shared ancestor incorrectly active', lambda r: item(r, 'diamond')['events'][11]['active'].append('viewer'), 'diamond:event11:active')
    mutate('direct permission removed from inherited', lambda r: item(r, 'diamond').update(inherited_permissions=['audit', 'write']), 'diamond:inherited_permissions')
    mutate('duplicated permission source', lambda r: item(r, 'diamond')['permission_sources']['read'].append('viewer'), 'diamond:source-role-sets')
    mutate('cycle path without valid return edge', lambda r: item(r, 'cycle')['diagnostic'].update(cycle_path=['lead', 'writer', 'lead']), 'cycle:cycle-edges')
    mutate('partial rejection result leaked', lambda r: item(r, 'cycle').update(effective_permissions=[]), 'cycle:no-partial-permission-publication')
    mutate('unknown role mislabeled', lambda r: item(r, 'unknown-role').update(reason='other-rejection'), 'unknown-role:reason')
    mutate('fault misclassified as input error', lambda r: item(r, 'diamond-visited-fault').update(classification='input-error'), 'diamond-visited-fault:classification')
    report = {'project': 'Atlas', 'passed': all(c['passed'] for c in checks + mutations), 'check_count': len(checks),
              'checks': checks, 'mutations': mutations, 'raw_sha256': sha(args.raw), 'expected_sha256': sha(ROOT / 'expected.json'),
              'verifier_sha256': sha(Path(__file__)), 'new_target_runs': 0,
              'scope': 'Saved finite cases and targeted in-memory semantic mutations; root execution/cleanup checked separately.'}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
