#!/usr/bin/env python3
"""Atlas: verify saved calculations using codeword distance, not the producer decoder."""
import argparse
import ast
from collections import Counter
import hashlib
from itertools import product
import json
from pathlib import Path

from oracle import codebook, minimum_distance, nearest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', type=Path, required=True)
    args = parser.parse_args()
    result = json.loads((args.record / 'results.json').read_text())
    fixed = json.loads((args.record / 'inputs/expected.json').read_text())
    checks = 0
    failures = []

    def equal(name, got, wanted):
        nonlocal checks
        checks += 1
        if got != wanted:
            failures.append({'name': name, 'actual': got, 'wanted': wanted})

    equal('total main cases', len(result['rows']), 1056)
    equal('unique case IDs', len({row['id'] for row in result['rows']}), 1056)
    equal('two separate outside examples', len(result['outsideGuaranteeExamples']), 2)
    for name, digest in result['inputSha256'].items():
        equal('snapshot digest ' + name, hashlib.sha256((args.record / 'inputs' / name).read_bytes()).hexdigest(), digest)
    tree = ast.parse((args.record / 'inputs/codec.py').read_text())
    for fn in [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('decode7', 'decode8')]:
        equal(fn.name + ' takes only received bits', [a.arg for a in fn.args.args], ['received'])
    books = {scheme: codebook(n) for scheme, n in (('hamming7', 7), ('secded8', 8))}
    for scheme, book in books.items():
        equal(scheme + ' 16 valid codewords', len(book), 16)
        equal(scheme + ' minimum distance', minimum_distance(book), fixed['minimumDistances'][scheme])
    for row in result['rows'] + result['outsideGuaranteeExamples']:
        label, scheme, message = row['id'], row['scheme'], row['message']
        sent = books[scheme][message]
        equal(label + ' encoder', row['sent'], sent)
        received = ''.join(str(int(b) ^ (i in row['errors'])) for i, b in enumerate(sent, 1))
        equal(label + ' channel', row['decoder']['received'], received)
        answer = nearest(received, books[scheme])
        for key in ('action', 'flip', 'corrected', 'decoded'):
            equal(label + ' distance decoder ' + key, row['decoder'][key], answer[key])
        q = sum(int(b) for b in received) % 2 if scheme == 'secded8' else None
        checks_bits = [sum(int(received[p-1]) for p in positions) % 2 for positions in ((1,3,5,7),(2,3,6,7),(4,5,6,7))]
        s = checks_bits[0] + 2 * checks_bits[1] + 4 * checks_bits[2]
        equal(label + ' parity equations', (row['decoder']['syndrome'], row['decoder']['overall']), (s, q))
        equal(label + ' check display order', row['decoder']['syndromeBits'], f'{s:03b}')
        equal(label + ' answer kept outside decoder', row['answerCheck']['matchesOriginal'], None if answer['decoded'] is None else answer['decoded'] == message)
        if answer['decoded'] is None:
            equal(label + ' refusal does not expose corrected data', row['decoder']['postSyndrome'], None)
            equal(label + ' refusal does not expose post parity', row['decoder']['postOverall'], None)
        else:
            equal(label + ' accepted codeword parity', row['decoder']['postSyndrome'], 0)
            equal(label + ' accepted overall parity', row['decoder']['postOverall'], 0 if scheme == 'secded8' else None)
    totals = {}
    for scheme in books:
        rows = [r for r in result['rows'] if r['scheme'] == scheme]
        totals[scheme] = {'rows': len(rows), **dict(Counter(r['decoder']['action'] for r in rows)),
                         'sameMessage': sum(r['answerCheck']['matchesOriginal'] is True for r in rows),
                         'wrongMessage': sum(r['answerCheck']['matchesOriginal'] is False for r in rows),
                         'withheldMessage': sum(r['answerCheck']['matchesOriginal'] is None for r in rows)}
        equal(scheme + ' hand totals', totals[scheme], fixed['expectedTotals'][scheme])
        equal(scheme + ' messages covered', sorted({r['message'] for r in rows}), [f'{n:04b}' for n in range(16)])
        for message in (f'{n:04b}' for n in range(16)):
            selected = [r for r in rows if r['message'] == message]
            equal(scheme + '/' + message + ' error-weight coverage', dict(Counter(len(r['errors']) for r in selected)), {0:1,1:len(books[scheme][message]),2:28 if scheme=='secded8' else 21})
    for expected in fixed['fixedExamples'] + fixed['outsideGuaranteeExamples']:
        rows = result['outsideGuaranteeExamples'] if len(expected['errors']) > 2 else result['rows']
        row = next(r for r in rows if (r['scheme'],r['message'],r['errors']) == (expected['scheme'],expected['message'],expected['errors']))
        projection = {**{k: row[k] for k in ('scheme','message','errors','sent')}, **row['decoder'], **row['answerCheck']}
        for name, wanted in expected.items(): equal(row['id'] + ' hand example ' + name, projection[name], wanted)
    all_received = {}
    for scheme, n in (('hamming7',7),('secded8',8)):
        distribution = Counter()
        for word in product('01',repeat=n):
            answer=nearest(''.join(word),books[scheme]);distribution[(answer['minimumDistance'],answer['nearestCount'])]+=1
        all_received[scheme]=[{'minimumDistance':k[0],'nearestCount':k[1],'receivedWordCount':v} for k,v in sorted(distribution.items())]
    equal('8bit all-received distance distribution',all_received['secded8'],[{'minimumDistance':0,'nearestCount':1,'receivedWordCount':16},{'minimumDistance':1,'nearestCount':1,'receivedWordCount':128},{'minimumDistance':2,'nearestCount':4,'receivedWordCount':112}])
    print(json.dumps({'Atlas':'SECDED independent-algorithm verification','kind':'author_separate_distance_check','differentReviewer':False,'producerImported':False,'passed':not failures,'checkCount':checks,'failures':failures,'totals':totals,'minimumDistances':{s:minimum_distance(b) for s,b in books.items()},'allReceivedDistribution':all_received,'resultsSha256':hashlib.sha256((args.record/'results.json').read_bytes()).hexdigest()},ensure_ascii=False,indent=2))
    return 0 if not failures else 1


if __name__ == '__main__':
    raise SystemExit(main())
