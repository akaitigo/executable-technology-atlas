"""Finite role closure model. No authentication, resource access, or expected-table import."""
from copy import deepcopy


def validate(graph, grants, requested_role, mode):
    if type(graph) is not dict or not 1 <= len(graph) <= 4:
        raise ValueError('graph must contain one to four roles')
    if type(grants) is not dict or set(grants) != set(graph):
        raise ValueError('grant keys must match graph')
    if type(requested_role) is not str or mode not in ('stack-checked', 'visited-only-fault'):
        raise ValueError('invalid role/mode input')
    for role, targets in graph.items():
        if type(role) is not str or type(targets) is not list or len(targets) > 4:
            raise ValueError('invalid adjacency')
        if any(type(x) is not str or x not in graph for x in targets) or len(set(targets)) != len(targets):
            raise ValueError('unknown or duplicated inheritance target')
        permissions = grants[role]
        if type(permissions) is not list or len(permissions) > 8 or any(type(x) is not str for x in permissions):
            raise ValueError('invalid grants')


def resolve(graph, grants, requested_role, mode):
    validate(graph, grants, requested_role, mode)
    visited, active, completed, events = [], [], [], []
    rejection = {'reason': None, 'cycle_path': None, 'reported_path': None}

    def emit(action, role, target=None):
        events.append(deepcopy({'index': len(events), 'action': action, 'role': role, 'target': target,
                                'active': active, 'visited_order': visited, 'completed_order': completed,
                                'cycle_path': rejection['cycle_path'], 'reported_path': rejection['reported_path']}))

    def visit(role):
        if mode == 'stack-checked' and role in active:
            rejection.update(reason='active-cycle', cycle_path=active[active.index(role):] + [role])
            emit('REJECT_CYCLE', role)
            return False
        if mode == 'visited-only-fault' and role in visited:
            rejection.update(reason='visited-as-cycle', reported_path=active + [role])
            emit('REJECT_REVISIT', role)
            return False
        if role in visited:
            emit('REUSE', role)
            return True
        visited.append(role)
        active.append(role)
        emit('ENTER', role)
        for inherited in graph[role]:
            emit('EDGE', role, inherited)
            if not visit(inherited):
                return False
        active.pop()
        completed.append(role)
        emit('LEAVE', role)
        return True

    emit('START', requested_role)
    result = dict.fromkeys(['reachable_set', 'reachable_order', 'direct_permissions', 'inherited_permissions',
                            'overlap_permissions', 'effective_permissions', 'permission_sources'])
    if requested_role not in graph:
        rejection['reason'] = 'unknown-role'
        emit('REJECT_UNKNOWN', requested_role)
        success = False
    else:
        success = visit(requested_role)
    if success:
        direct = set(grants[requested_role])
        inherited = set()
        for role in visited:
            if role != requested_role:
                inherited.update(grants[role])
        effective = direct | inherited
        result.update(reachable_set=sorted(visited), reachable_order=list(visited), direct_permissions=sorted(direct),
                      inherited_permissions=sorted(inherited), overlap_permissions=sorted(direct & inherited),
                      effective_permissions=sorted(effective),
                      permission_sources={permission: sorted(role for role in visited if permission in grants[role])
                                          for permission in sorted(effective)})
        emit('ACCEPT', requested_role)
    result.update(requested_role=requested_role, mode=mode, status='accepted' if success else 'rejected',
                  reason='closure-resolved' if success else rejection['reason'],
                  classification='intentional-false-positive' if mode == 'visited-only-fault' else 'resolved' if success else 'expected-rejection',
                  diagnostic=deepcopy({'entered_order': visited, 'completed_order': completed, 'active_at_stop': active,
                                       'cycle_path': rejection['cycle_path'], 'reported_path': rejection['reported_path']}),
                  events=events)
    return result
