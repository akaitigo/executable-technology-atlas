"""Saved-artifact checks against pre-implementation hand rows; no model import."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def inspect(raw):
    expected = json.loads((ROOT / 'expected.json').read_text())
    fixture = json.loads((ROOT / 'inputs/cases.json').read_text())
    checks = []
    def ck(label, passed):
        checks.append({'label': label, 'passed': bool(passed)})
    ck('complete', raw.get('complete') and not raw.get('errors') and raw.get('model_cases_started') == 11)
    ck('input-bytes', raw.get('fixture') == fixture)
    ck('source-bytes', raw.get('source_unchanged') and raw.get('source_sha256') == {n: sha(ROOT / n) for n in ['cache_model.py', 'run.py', 'inputs/cases.json']})
    execution = raw['execution']
    ck('recorded-priority', execution['nice_before'] >= 10 and execution['nice_after'] >= 10 and execution['pid'] > 0)
    ck('result-order', [r['id'] for r in raw['results']] == [r['id'] for r in expected['results']])
    # Independent sequential byte recurrence, not the model's multiplication function.
    memory = [3]
    for _ in range(255):
        memory.append((memory[-1] + 17) % 256)
    for result, hand in zip(raw['results'], expected['results']):
        tag = hand['id']
        mode = tag.split('/')[1]
        ways, sets = (1, 4) if mode == 'direct' else (2, 2)
        cold = {'sets': [[{'valid': False, 'block': None, 'tag': None, 'bytes': []} for _ in range(ways)] for _ in range(sets)], 'lru': [[] for _ in range(sets)]}
        ck(tag + ':initial', result['initial'] == cold)
        ck(tag + ':classification', result['classification'] == ('intentional-lru-fault' if mode.endswith('no-hit-touch') else 'normal'))
        ck(tag + ':geometry', result['geometry'] == {'capacity_bytes': 16, 'line_bytes': 4, 'line_count': 4, 'set_count': sets, 'ways': ways, 'offset_bits': 2, 'set_bits': 2 if ways == 1 else 1, 'tag_bits': 4 if ways == 1 else 5})
        ck(tag + ':row-count', len(result['events']) == len(hand['rows']))
        previous = cold
        for index, (event, row) in enumerate(zip(result['events'], hand['rows']), 1):
            label = tag + ':row' + str(index)
            primitive = ['address', 'block', 'set', 'tag', 'offset', 'hit', 'way', 'victim_block', 'returned_byte', 'fetched_bytes']
            ck(label + ':manual-fields', all(event[k] == row[k] and type(event[k]) is type(row[k]) for k in primitive))
            ck(label + ':continuity', event['step'] == index and event['before'] == previous)
            selected = row['set']
            before, after = event['before'], event['after']
            ck(label + ':selected-blocks', [x['block'] for x in before['sets'][selected]] == row['blocks_before'] and [x['block'] for x in after['sets'][selected]] == row['blocks_after'])
            ck(label + ':manual-recency', before['lru'][selected] == row['lru_before'] and after['lru'][selected] == row['lru_after'])
            ck(label + ':other-sets', all(before['sets'][s] == after['sets'][s] and before['lru'][s] == after['lru'][s] for s in range(sets) if s != selected))
            good = True
            for state in [before, after]:
                good &= len(state['sets']) == sets and len(state['lru']) == sets
                for s, lines in enumerate(state['sets']):
                    good &= len(lines) == ways
                    valid = []
                    for w, line in enumerate(lines):
                        if line['valid'] is True:
                            block = line['block']; valid.append(w)
                            good &= type(block) is int and 0 <= block < 64 and block % sets == s and line['tag'] == block // sets
                            good &= line['bytes'] == memory[block * 4:block * 4 + 4]
                        else:
                            good &= line == {'valid': False, 'block': None, 'tag': None, 'bytes': []}
                    good &= sorted(state['lru'][s]) == valid
            ck(label + ':whole-state-data', good)
            ck(label + ':returned-memory-byte', event['returned_byte'] == memory[row['address']] == after['sets'][selected][row['way']]['bytes'][row['offset']])
            ck(label + ':fill-and-touch', event['fill_range'] == (None if row['hit'] else [row['block'] * 4, row['block'] * 4 + 3]) and event['recency_touched'] == (not row['hit'] or mode != 'two-way-no-hit-touch'))
            reason = 'valid-tag-hit' if row['hit'] else 'fill-invalid' if row['victim_block'] is None else 'replace-lru'
            ck(label + ':decision', event['decision'] == reason)
            previous = after
        ck(tag + ':final', result['final'] == previous)
        ck(tag + ':summary', result['summary'] == hand['summary'])
        ck(tag + ':summary-events', result['summary']['hits'] == sum(e['hit'] for e in result['events']) and result['summary']['misses'] == sum(not e['hit'] for e in result['events']) and result['summary']['evictions'] == sum(e['victim_block'] is not None for e in result['events']) and result['summary']['fetched_bytes'] == sum(e['fetched_bytes'] for e in result['events']))
    return checks


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('raw', type=Path); args = ap.parse_args()
    raw = json.loads(args.raw.read_text()); checks = inspect(raw); mutations = []
    def result(r, name):
        return next(x for x in r['results'] if x['id'] == name)
    def mutate(name, edit, required):
        altered = copy.deepcopy(raw); edit(altered)
        failed = [c['label'] for c in inspect(altered) if not c['passed']]
        mutations.append({'name': name, 'required_label': required, 'failed_labels': failed, 'passed': required in failed})
    mutate('wrong tag', lambda r: result(r, 'offsets/two-way-lru')['events'][4].update(tag=15), 'offsets/two-way-lru:row5:manual-fields')
    mutate('wrong selected way', lambda r: result(r, 'conflict/two-way-lru')['events'][1].update(way=0), 'conflict/two-way-lru:row2:manual-fields')
    mutate('wrong victim', lambda r: result(r, 'hit-recency/two-way-lru')['events'][3].update(victim_block=0), 'hit-recency/two-way-lru:row4:manual-fields')
    mutate('hit recency lost', lambda r: result(r, 'hit-recency/two-way-lru')['events'][2]['after']['lru'].__setitem__(0, [0, 1]), 'hit-recency/two-way-lru:row3:manual-recency')
    mutate('wrong byte', lambda r: result(r, 'offsets/direct')['events'][4].update(returned_byte=0), 'offsets/direct:row5:returned-memory-byte')
    mutate('wrong fetch byte count', lambda r: result(r, 'conflict/direct')['events'][0].update(fetched_bytes=1), 'conflict/direct:row1:manual-fields')
    mutate('empty rate zero', lambda r: result(r, 'empty/two-way-lru')['summary'].update(hit_rate=0), 'empty/two-way-lru:summary')
    report = {'project': 'Atlas', 'passed': all(c['passed'] for c in checks + mutations), 'check_count': len(checks), 'checks': checks, 'mutations': mutations, 'raw_sha256': sha(args.raw), 'expected_sha256': sha(ROOT / 'expected.json'), 'verifier_sha256': sha(Path(__file__)), 'new_target_runs': 0, 'scope': 'Saved model output and targeted semantic mutations; root execution/cleanup evidence is checked separately.'}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
