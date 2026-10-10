"""Atlas: annotated Int/arrow judgments, not a type-safety proof or a runtime."""
import copy
import re


class InputRefused(ValueError):
    pass


def require(ok, reason):
    if not ok:
        raise InputRefused(reason)


def validate(term, budget):
    require(type(budget) is int and 0 <= budget <= 16, 'budget 0..16; bool excluded')
    fields = {'Int': {'kind', 'value'}, 'Var': {'kind', 'name'},
              'Fn': {'kind', 'param', 'param_type', 'body'},
              'Call': {'kind', 'fn', 'arg'}, 'Add': {'kind', 'left', 'right'}}
    count = 0
    def check_type(t, depth=1):
        require(depth <= 4, 'type depth limit 4')
        if t == 'Int':
            return
        require(type(t) is dict and set(t) == {'arrow'} and type(t['arrow']) is list and len(t['arrow']) == 2,
                'type must be Int or exact arrow pair')
        for child in t['arrow']:
            check_type(child, depth + 1)
    def visit(node, depth, bound):
        nonlocal count
        count += 1
        require(count <= 64 and depth <= 16, 'AST node/depth limit')
        require(type(node) is dict and type(node.get('kind')) is str, 'AST object/kind')
        kind = node['kind']
        require(kind in fields and set(node) == fields[kind], 'AST subset/exact fields')
        if kind == 'Int':
            require(type(node['value']) is int and -1000 <= node['value'] <= 1000, 'integer literal; bool excluded')
        elif kind in ('Fn', 'Var'):
            name = node['param' if kind == 'Fn' else 'name']
            require(type(name) is str and re.fullmatch(r'[a-z][a-z0-9_]{0,15}', name) is not None, 'name syntax')
            if kind == 'Var':
                require(name in bound, 'closed input required')
            else:
                check_type(node['param_type'])
                visit(node['body'], depth + 1, bound | {name})
        else:
            for key in (('left', 'right') if kind == 'Add' else ('fn', 'arg')):
                visit(node[key], depth + 1, bound)
    visit(term, 1, set())
    return count


def erase(term):
    """Remove only Fn.param_type; preserve every other AST field and position."""
    return {key: erase(value) if isinstance(value, dict) else copy.deepcopy(value)
            for key, value in term.items() if key != 'param_type'}


def derive(term, context=None, path='$'):
    """Synthesize a type from explicit parameter annotations on validated syntax.

    Premise trees record logical dependencies and deterministic checking order;
    they are not runtime evaluation events or proof of general soundness.
    """
    context = {} if context is None else context
    kind = term['kind']
    record = {'path': path, 'rule': 'T_' + kind, 'context': copy.deepcopy(context),
              'status': 'accepted', 'type': None, 'premises': [], 'rejection': None, 'unvisited': []}
    def accept(t):
        record['type'] = copy.deepcopy(t)
        return record
    def reject(reason, unvisited=()):
        record.update(status='rejected', type=None, rejection=copy.deepcopy(reason), unvisited=list(unvisited))
        return record
    def child(key, env=context):
        node = derive(term[key], env, path + '.' + key)
        record['premises'].append(node)
        return node
    def mismatch(code, location, expected, actual):
        return {'code': code, 'path': location, 'expected': expected, 'actual': actual}
    if kind == 'Int':
        return accept('Int')
    if kind == 'Var':
        # Validation requires closed inputs; each enclosing Fn supplies its type.
        return accept(context[term['name']])
    if kind == 'Fn':
        inner = dict(context)
        inner[term['param']] = copy.deepcopy(term['param_type'])
        body = child('body', inner)
        if body['status'] == 'rejected':
            return reject(body['rejection'])
        return accept({'arrow': [term['param_type'], body['type']]})
    if kind == 'Call':
        fn = child('fn')
        if fn['status'] == 'rejected':
            return reject(fn['rejection'], [path + '.arg'])
        if fn['type'] == 'Int':
            return reject(mismatch('not-arrow', path + '.fn', 'Arrow', fn['type']), [path + '.arg'])
        arg = child('arg')
        if arg['status'] == 'rejected':
            return reject(arg['rejection'])
        domain, codomain = fn['type']['arrow']
        if arg['type'] != domain:
            return reject(mismatch('domain-mismatch', path + '.arg', domain, arg['type']))
        return accept(codomain)
    if kind == 'Add':
        for key in ['left', 'right']:
            operand = child(key)
            later = [path + '.right'] if key == 'left' else []
            if operand['status'] == 'rejected':
                return reject(operand['rejection'], later)
            if operand['type'] != 'Int':
                return reject(mismatch('int-required', path + '.' + key, 'Int', operand['type']), later)
        return accept('Int')
    raise RuntimeError('unexpected validated kind')
