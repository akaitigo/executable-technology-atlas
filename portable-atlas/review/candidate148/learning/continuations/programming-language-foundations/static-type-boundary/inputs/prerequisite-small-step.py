"""Atlas: bounded closed-term small-step model; not a formal proof engine."""
import copy
import re


class InputRefused(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise InputRefused(reason)


def free_names(term):
    kind = term['kind']
    if kind == 'Int':
        return set()
    if kind == 'Var':
        return {term['name']}
    if kind == 'Fn':
        return free_names(term['body']) - {term['param']}
    keys = ('left', 'right') if kind == 'Add' else ('fn', 'arg')
    return free_names(term[keys[0]]) | free_names(term[keys[1]])


def validate(term, budget):
    require(type(budget) is int and 0 <= budget <= 16, 'budget must be an integer in 0..16; bool excluded')
    fields = {'Int': {'kind', 'value'}, 'Var': {'kind', 'name'},
              'Fn': {'kind', 'param', 'body'}, 'Call': {'kind', 'fn', 'arg'},
              'Add': {'kind', 'left', 'right'}}
    count = 0
    def visit(node, depth):
        nonlocal count
        count += 1
        require(count <= 64 and depth <= 16, 'input AST limit')
        require(type(node) is dict and type(node.get('kind')) is str, 'AST object/kind')
        kind = node['kind']
        require(kind in fields and set(node) == fields[kind], 'AST subset or exact fields')
        if kind == 'Int':
            require(type(node['value']) is int and -1000 <= node['value'] <= 1000, 'input integer literal; bool excluded')
        if kind in ('Var', 'Fn'):
            name = node['name' if kind == 'Var' else 'param']
            require(type(name) is str and re.fullmatch(r'[a-z][a-z0-9_]{0,15}', name) is not None, 'name syntax')
        if kind == 'Fn':
            visit(node['body'], depth + 1)
        elif kind in ('Add', 'Call'):
            for key in (('left', 'right') if kind == 'Add' else ('fn', 'arg')):
                visit(node[key], depth + 1)
    visit(term, 1)
    require(not free_names(term), 'only closed input terms are supported')
    return count


def is_value(term):
    return term['kind'] in ('Int', 'Fn')


def substitute_closed(term, name, value):
    """Only a closed value may replace free occurrences of the parameter."""
    if not is_value(value) or free_names(value):
        raise RuntimeError('internal substitution premise: closed value required')
    kind = term['kind']
    if kind == 'Int':
        return copy.deepcopy(term)
    if kind == 'Var':
        return copy.deepcopy(value if term['name'] == name else term)
    if kind == 'Fn':
        if term['param'] == name:
            return copy.deepcopy(term)
        return {'kind': 'Fn', 'param': term['param'],
                'body': substitute_closed(term['body'], name, value)}
    keys = ('left', 'right') if kind == 'Add' else ('fn', 'arg')
    return {'kind': kind, **{key: substitute_closed(term[key], name, value) for key in keys}}


def propose_step(term, path='$'):
    """Return one possible step plus its rule derivation, or a stuck reason.

    The returned AST is only a proposal. The bounded driver decides whether to
    apply it; probing after the budget is exhausted is not an applied transition.
    """
    kind = term['kind']
    if is_value(term):
        return None, None
    if kind == 'Var':
        return None, {'code': 'unbound-variable', 'path': path}

    def descend(key, rule):
        child, reason = propose_step(term[key], path + '.' + key)
        if child is None:
            return None, reason
        after = copy.deepcopy(term)
        after[key] = child['after']
        return {'after': after, 'rule_chain': [rule] + child['rule_chain'],
                'redex_path': child['redex_path'],
                'redex_before': child['redex_before'], 'redex_after': child['redex_after']}, None

    def primitive(after, rule):
        return {'after': after, 'rule_chain': [rule], 'redex_path': path,
                'redex_before': copy.deepcopy(term), 'redex_after': copy.deepcopy(after)}, None

    if kind == 'Add':
        if not is_value(term['left']):
            return descend('left', 'AddLeft')
        if not is_value(term['right']):
            return descend('right', 'AddRight')
        if term['left']['kind'] != 'Int' or term['right']['kind'] != 'Int':
            return None, {'code': 'addition-type', 'path': path}
        return primitive({'kind': 'Int', 'value': term['left']['value'] + term['right']['value']}, 'AddInts')
    if kind == 'Call':
        if not is_value(term['fn']):
            return descend('fn', 'CallFn')
        if term['fn']['kind'] != 'Fn':
            return None, {'code': 'not-callable', 'path': path}
        if not is_value(term['arg']):
            return descend('arg', 'CallArg')
        return primitive(substitute_closed(term['fn']['body'], term['fn']['param'], term['arg']), 'Beta')
    raise RuntimeError('unexpected validated kind')


def run(term, budget):
    validate(term, budget)
    current = copy.deepcopy(term)
    states, transitions = [copy.deepcopy(current)], []
    while True:
        if is_value(current):
            status, reason, next_rule, next_path = 'value', None, None, None
            break
        proposal, reason = propose_step(current)
        if proposal is None:
            status, next_rule, next_path = 'stuck', None, None
            break
        if len(transitions) == budget:
            status, next_rule, next_path = 'budget_exhausted', proposal['rule_chain'], proposal['redex_path']
            reason = None
            break
        transitions.append({'index': len(transitions) + 1, 'before': copy.deepcopy(current), **copy.deepcopy(proposal)})
        current = proposal['after']
        states.append(copy.deepcopy(current))
    value = current['value'] if status == 'value' and current['kind'] == 'Int' else None
    return {'status': status, 'budget': budget, 'applied_steps': len(transitions),
            'remaining_budget': budget - len(transitions), 'states': states,
            'transitions': transitions, 'final_term': copy.deepcopy(current),
            'value': value, 'function_value': copy.deepcopy(current) if status == 'value' and current['kind'] == 'Fn' else None,
            'reason': reason, 'unapplied_next_rule': next_rule, 'unapplied_next_redex_path': next_path,
            'scope': 'Fixed closed-term model; probes are not applied steps; no termination or equivalence proof'}
