"""Own fixed cost scope and business denominator, exact Fraction arithmetic."""
from fractions import Fraction

def validate(f):
    if f['scope']!='compute-plus-allocated-shared-cent-for-closed-batch' or f['business_unit']!='successful-request':return 'UNKNOWN_SCOPE'
    if f['policy'] not in ['strict','all-attempts-as-success']:return 'UNKNOWN_POLICY'
    for name in ['baseline','candidate']:
        p=f[name]
        if any(type(p[k]) is not int or not 0<=p[k]<=1000 for k in ['attempts','success']):return 'INVALID_COUNT'
        if p['success']>p['attempts']:return 'SUCCESS_EXCEEDS_ATTEMPTS'
        if [c['id'] for c in p['costs']]!=['compute','allocated-shared']:return 'COST_SCOPE_MISMATCH'
        if any(type(c['cents']) is not int or not 0<=c['cents']<=100000 for c in p['costs']):return 'INVALID_CENT'
        if any(c['currency']!='XCU' for c in p['costs']):return 'CURRENCY_MISMATCH'
    return None

def encoded(value):
    return None if value is None else dict(numerator=value.numerator,denominator=value.denominator,exact=str(value))

def relative(a,b):
    if a is None or b is None or a==0:return None,None
    ratio=b/a;return ratio,ratio-1

def run(f):
    reason=validate(f)
    if reason:return dict(status='INPUT_REJECTED',reason=reason,calculation_started=False,periods={},comparison=None)
    bad=f['policy']=='all-attempts-as-success';periods={};units={};totals={};true_units={}
    for name in ['baseline','candidate']:
        p=f[name];total=sum(c['cents'] for c in p['costs']);denominator=p['attempts'] if bad else p['success'];unit=Fraction(total,denominator) if denominator else None
        periods[name]=dict(currency='XCU',cost_scope=f['scope'],source_costs=p['costs'],total_cents=total,attempts=p['attempts'],success=p['success'],failed_attempts=p['attempts']-p['success'],declared_unit='cent_per_successful_request',denominator_basis='attempts' if bad else 'success',denominator_used=denominator,unit_cost=encoded(unit),unit_reason='ZERO_DENOMINATOR' if unit is None else None)
        totals[name]=Fraction(total);units[name]=unit;true_units[name]=Fraction(total,p['success']) if p['success'] else None
    total_ratio,total_change=relative(totals['baseline'],totals['candidate']);unit_ratio,unit_change=relative(units['baseline'],units['candidate']);true_ratio,_=relative(true_units['baseline'],true_units['candidate']);claim=bool(bad and unit_ratio is not None and unit_ratio<1)
    status='BAD_ACCEPTED' if bad else 'UNDEFINED_UNIT' if any(v is None for v in units.values()) else 'UNDEFINED_COMPARISON' if total_ratio is None or unit_ratio is None else 'COMPARED'
    return dict(status=status,calculation_started=True,periods=periods,comparison=dict(total_ratio=encoded(total_ratio),total_change=encoded(total_change),unit_ratio=encoded(unit_ratio),unit_change=encoded(unit_change),total_ratio_reason='ZERO_BASELINE_TOTAL' if total_ratio is None else None,unit_ratio_reason='UNDEFINED_UNIT' if any(v is None for v in units.values()) else 'ZERO_BASELINE_UNIT' if unit_ratio is None else None),bad_judgment=dict(enabled=bad,claims_unit_improved=claim,rule_failed=bool(claim and true_ratio is not None and true_ratio>=1)))
