"""Synthetic ratecard only; fixed Decimal context; no float, billing API or real prices."""
import copy
import re
from datetime import datetime, timezone
from decimal import Context, Decimal, FloatOperation, ROUND_FLOOR, ROUND_HALF_UP, localcontext

DECIMAL_CONTEXT=Context(prec=28,rounding=ROUND_HALF_UP,Emin=-999999,Emax=999999)
DECIMAL_CONTEXT.traps[FloatOperation]=True
TEAMS=('A','B','C')

class InvalidInput(ValueError): pass

def number(text):
    # Small finite input domain ensures exact Decimal products stay within precision 28.
    if type(text) is not str or not re.fullmatch(r'-?\d{1,6}(?:\.\d{1,6})?',text):
        raise InvalidInput('invalid-numeric-string')
    return Decimal(text)

def cents(value):
    return int((value.quantize(Decimal('0.01'),rounding=ROUND_HALF_UP)*100).to_integral_exact())

def calculate(data):
    raw=[]
    def log(stage,**details):
        raw.append({'at':datetime.now(timezone.utc).isoformat(),'stage':stage,**copy.deepcopy(details)})
    context={'precision':28,'rounding':'ROUND_HALF_UP','Emin':-999999,'Emax':999999,'FloatOperation':'trapped','binary_float':'prohibited','money_unit':'fictional XCU; 100 cents = 1 XCU'}
    log('input',input=data,decimal_context=context,scope='synthetic fixed ratecard/usage; not market prices/tax/financial advice')
    with localcontext(DECIMAL_CONTEXT):
        try:
            if data['policy'] not in ('conserved','naive'): raise InvalidInput('invalid-policy')
            pool=number(data['shared_amount'])
            if pool<0: raise InvalidInput('negative-shared-cost')
            if not 0<=len(data['usage'])<=8: raise InvalidInput('invalid-usage-size')
            ids=set()
            rates={sku:number(rate) for sku,rate in data['ratecard'].items()}
            if any(rate<0 for rate in rates.values()): raise InvalidInput('negative-rate')
            validated=[]
            for usage in data['usage']:
                if not isinstance(usage.get('id'),str) or not usage['id'] or usage['id'] in ids: raise InvalidInput('duplicate-or-invalid-usage-id')
                ids.add(usage['id'])
                quantity=number(usage['quantity'])
                if quantity<=0: raise InvalidInput('invalid-quantity')
                if usage['sku'] not in rates: raise InvalidInput('unknown-sku')
                validated.append((usage,quantity,rates[usage['sku']]))
            weights=data['weights']
            if any(team not in TEAMS or type(weight) is not int or not 1<=weight<=1000 for team,weight in weights.items()): raise InvalidInput('invalid-weight')
        except InvalidInput as error:
            log('validation-rejected',reason=str(error),state_unchanged=True)
            return {'status':str(error),'context':context,'tree':None,'raw':raw}
        log('validation-accepted',usage_rows=len(validated),teams=TEAMS,weights=weights)
        teams={team:{'direct_cents':0,'shared_cents':0} for team in TEAMS}
        unallocated={'direct_cents':0,'shared_cents':0,'reasons':[]}
        direct=[]
        for usage,quantity,rate in validated:
            exact=quantity*rate; charged=cents(exact)
            tag=usage.get('team')
            destination=tag if tag in TEAMS else 'unallocated'
            reason=None if destination!='unallocated' else 'missing-tag' if tag is None or tag=='' else 'unknown-tag'
            record={'id':usage['id'],'sku':usage['sku'],'quantity':str(quantity),'rate_XCU':str(rate),'exact_XCU':str(exact),'charged_cents':charged,'destination':destination,'reason':reason}
            direct.append(record)
            if destination=='unallocated':
                unallocated['direct_cents']+=charged
                unallocated['reasons'].append({'id':usage['id'],'reason':reason,'cents':charged})
            else: teams[destination]['direct_cents']+=charged
            log('direct-line',**record)
        pool_cents=cents(pool)
        log('source-charge',direct_cents=sum(x['charged_cents'] for x in direct),shared_exact_XCU=str(pool),shared_charged_cents=pool_cents,rule='direct lines and shared source individually HALF_UP to cents')
        shares=[]
        if not weights:
            unallocated['shared_cents']=pool_cents
            unallocated['reasons'].append({'id':'shared','reason':'no-allocation-basis','cents':pool_cents})
            log('shared-unallocated',cents=pool_cents,reason='no-allocation-basis')
            residual=0; ranking=[]
        else:
            denominator=sum(weights.values())
            for team in sorted(weights):
                exact=Decimal(pool_cents)*Decimal(weights[team])/Decimal(denominator)
                floor=int(exact.to_integral_value(rounding=ROUND_FLOOR))
                fraction=exact-Decimal(floor)
                shares.append({'team':team,'weight':weights[team],'denominator':denominator,'exact_share_cents':str(exact),'floor_cents':floor,'fractional_remainder':str(fraction)})
            residual=pool_cents-sum(x['floor_cents'] for x in shares)
            ranking=[x['team'] for x in sorted(shares,key=lambda x:(-Decimal(x['fractional_remainder']),x['team']))]
            log('share-basis',shares=shares,residual_cents=residual,remainder_order=ranking,tie_rule='fraction descending, team ID ascending')
            for share in shares:
                if data['policy']=='conserved':
                    extra=1 if share['team'] in ranking[:residual] else 0
                    assigned=share['floor_cents']+extra
                else:
                    extra=None
                    assigned=int(Decimal(share['exact_share_cents']).to_integral_value(rounding=ROUND_HALF_UP))
                teams[share['team']]['shared_cents']=assigned
                share.update({'extra_cents':extra,'assigned_cents':assigned})
                log('shared-leaf',**share,policy=data['policy'])
        source=sum(x['charged_cents'] for x in direct)+pool_cents
        assigned=sum(x['direct_cents']+x['shared_cents'] for x in teams.values())+unallocated['direct_cents']+unallocated['shared_cents']
        tree={'source_total_cents':source,'source_direct_cents':sum(x['charged_cents'] for x in direct),'source_shared_cents':pool_cents,'teams':teams,'unallocated':unallocated,'allocated_total_cents':assigned,'rounding_gap_cents':source-assigned,'shared_assigned_cents':sum(x['shared_cents'] for x in teams.values()),'direct_rows':direct,'shares':shares,'residual_cents':residual,'remainder_order':ranking}
        log('cost-tree',tree=tree,conserved=source==assigned)
        return {'status':'calculated','context':context,'tree':tree,'raw':raw}
