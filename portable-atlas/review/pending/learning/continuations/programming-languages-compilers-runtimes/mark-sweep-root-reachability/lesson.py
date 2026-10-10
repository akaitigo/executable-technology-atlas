from collector import collect
from oracle import reachable
def run(fixture,mode):
    row=collect(fixture['objects'],fixture['roots'],mode)
    live=reachable(fixture['objects'],fixture['roots'])
    premature=sorted(set(live)&set(row['reclaimed']))
    leaked=sorted(set(row['survivors'])-set(live))
    return dict(fixture=fixture['id'],objects=fixture['objects'],oracle_reachable=live,
                premature_reclaimed=premature,leaked=leaked,safe=not premature,
                matches_oracle=row['marked']==live and not leaked,**row)
