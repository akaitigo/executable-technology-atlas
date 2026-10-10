"""Atlas: finite retry classification, budget and logical-time readiness model."""

SPECS = [
    ('retryable-resume', ['TRANSIENT', 'SUCCESS'], 'on-terminal-failure'),
    ('nonretryable-stop', ['PERMANENT', 'SUCCESS'], 'on-terminal-failure'),
    ('retry-budget-exhausted', ['TRANSIENT', 'TRANSIENT', 'TRANSIENT'], 'on-terminal-failure'),
    ('premature-downstream-block', ['TRANSIENT', 'SUCCESS'], 'on-any-failure-sticky'),
]


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def validate(fixture, case_id):
    require(type(fixture) is dict and set(fixture) == {
        'title', 'schema', 'edge', 'b_success_value', 'd_multiplier',
        'retry_budget', 'retry_delay', 'attempt_duration', 'cases'}, 'SCHEMA')
    for name in ['schema', 'b_success_value', 'd_multiplier', 'retry_budget', 'retry_delay', 'attempt_duration']:
        require(type(fixture[name]) is int, 'INTEGER_REQUIRED')
    require(fixture['title'] == 'Atlas fixed retry readiness inputs' and
            fixture['schema'] == 1 and type(fixture['edge']) is list and fixture['edge'] == ['B', 'D'] and
            (fixture['b_success_value'], fixture['d_multiplier'], fixture['retry_budget'],
             fixture['retry_delay'], fixture['attempt_duration']) == (7, 2, 2, 2, 1), 'FIXED_INPUT')
    require(type(fixture['cases']) is list and len(fixture['cases']) == 4, 'CASE_SCHEMA')
    for case, (name, outcomes, mode) in zip(fixture['cases'], SPECS):
        require(type(case) is dict and set(case) == {'id', 'outcomes', 'downstream_mode'}, 'CASE_SCHEMA')
        require(type(case['outcomes']) is list and all(type(x) is str and x in
                ['TRANSIENT', 'PERMANENT', 'SUCCESS'] for x in case['outcomes']), 'FAILURE_LABEL')
        require(case['id'] == name and case['outcomes'] == outcomes and
                case['downstream_mode'] == mode, 'FIXED_CASE')
    require(type(case_id) is str and case_id in [s[0] for s in SPECS], 'UNKNOWN_CASE')
    return next(c for c in fixture['cases'] if c['id'] == case_id)


def execute(fixture, case_id):
    case = validate(fixture, case_id)  # No task start occurs before every input check.
    b_state, d_state = 'pending', 'pending'
    b_value = d_value = None
    remaining = fixture['retry_budget']
    due = b_active = d_active = None
    attempts = []; downstream = []; boundaries = []; failures = []; checks = []; violations = []
    for now in range(16):  # A hard finite bound, not a real-time scheduler.
        checked = met = None
        if b_active is not None and now == b_active['end']:
            outcome = b_active['outcome']
            if outcome == 'SUCCESS':
                b_value = fixture['b_success_value']
                b_active['value'] = b_value
                b_state = 'succeeded'
            else:
                retryable = outcome == 'TRANSIENT'
                planned = retryable and remaining > 0
                due = now + fixture['retry_delay'] if planned else None
                failures.append({'at': now, 'attempt': b_active['attempt'], 'error': outcome,
                    'retryable': retryable, 'remaining_retries': remaining, 'retry_planned': planned,
                    'next_due': due, 'terminal_reason': None if planned else
                    ('nonretryable' if not retryable else 'budget-exhausted')})
                b_state = 'retry-wait' if planned else 'failed'
                if planned and case['downstream_mode'] == 'on-any-failure-sticky':
                    d_state = 'blocked'
                    violations.append({'at': now, 'kind': 'downstream-finalized-before-upstream-terminal', 'downstream': 'D'})
            b_active = None
        if d_active is not None and now == d_active['end']:
            d_value = d_active['input'] * fixture['d_multiplier']
            d_active['value'] = d_value
            d_state = 'succeeded'; d_active = None
        if b_state == 'failed' and d_state == 'pending':
            d_state = 'blocked'
        if b_state == 'retry-wait':
            checked = due; met = now >= due
            checks.append({'at': now, 'due': due, 'eligible': met})
        if b_state == 'pending' or (b_state == 'retry-wait' and met):
            if attempts:
                require(remaining > 0, 'INTERNAL_BUDGET')
                remaining -= 1
            number = len(attempts) + 1
            require(number <= len(case['outcomes']), 'INTERNAL_OUTCOME')
            b_active = {'attempt': number, 'start': now, 'end': now + fixture['attempt_duration'],
                        'outcome': case['outcomes'][number - 1], 'value': None}
            attempts.append(b_active)
            b_state = 'running'; due = None
        if b_state == 'succeeded' and d_state == 'pending':
            d_active = {'attempt': 1, 'start': now, 'end': now + fixture['attempt_duration'],
                        'input': b_value, 'value': None}
            downstream.append(d_active); d_state = 'running'
        boundaries.append({'t': now, 'b_state': b_state, 'attempts_started': len(attempts),
            'retries_left': remaining, 'waiting_until': due, 'retry_due_checked': checked,
            'retry_time_met': met, 'd_state': d_state, 'b_value': b_value, 'd_value': d_value,
            'policy_violation': bool(violations)})
        if b_state in ['succeeded', 'failed'] and d_state in ['succeeded', 'blocked']:
            break
    else:
        raise RuntimeError('finite model did not terminate')
    status = 'policy-violation' if violations else ('succeeded' if d_state == 'succeeded' else 'failed')
    classification = 'INTENTIONAL_FAULT' if violations else ('NORMAL' if status == 'succeeded' else 'EXPECTED_TERMINAL_FAILURE')
    return {'id': case_id, 'boundaries': boundaries, 'b_attempts': attempts, 'd_attempts': downstream,
            'failure_decisions': failures, 'retry_checks': checks, 'workflow_status': status,
            'classification': classification, 'unreached_outcomes': case['outcomes'][len(attempts):],
            'policy_violations': violations, 'b_calls': len(attempts), 'd_calls': len(downstream)}
