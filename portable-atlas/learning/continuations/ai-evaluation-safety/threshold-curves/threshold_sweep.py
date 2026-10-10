"""Atlas: finite empirical thresholds, exact decimal comparisons, no model or AUC."""
from decimal import Decimal
from fractions import Fraction

def canonical(value):
    return format(value.normalize(), 'f')

def validate(raw):
    if type(raw) is not list or not 1 <= len(raw) <= 64:
        raise ValueError('one to 64 samples required')
    result=[];seen=set()
    for row in raw:
        if type(row) is not dict or set(row) != {'id','label','score'}:
            raise ValueError('exact id/label/score fields required')
        sample_id=row['id'];label=row['label'];score=row['score']
        if type(sample_id) is not str or not sample_id or sample_id in seen:
            raise ValueError('unique nonempty sample ID required')
        if type(label) is not int or label not in (0,1):
            raise ValueError('integer label 0 or 1 required')
        if type(score) not in (Decimal,str,int):
            raise ValueError('score must originate as an exact decimal, string, or integer')
        score=Decimal(score)
        if not score.is_finite() or not Decimal(0) <= score <= Decimal(1):
            raise ValueError('finite score in [0,1] required')
        seen.add(sample_id);result.append({'id':sample_id,'label':label,'score':score})
    return result

def ratio(numerator,denominator):
    return {'numerator':numerator,'denominator':denominator,
            'fraction':str(Fraction(numerator,denominator)) if denominator else None,
            'value':float(Fraction(numerator,denominator)) if denominator else None,
            'status':'defined' if denominator else 'undefined-zero-denominator'}

def sweep(samples):
    samples=validate(samples)
    boundaries=sorted({s['score'] for s in samples},reverse=True)
    prior=set();states=[]
    for ordinal,boundary in enumerate([None]+boundaries):
        predicted={s['id'] for s in samples if boundary is not None and s['score'] >= boundary}
        ids={key:[] for key in ['TP','FP','FN','TN']}
        for s in samples:
            key=('TP' if s['id'] in predicted else 'FN') if s['label']==1 else ('FP' if s['id'] in predicted else 'TN')
            ids[key].append(s['id'])
        ids={k:sorted(v) for k,v in ids.items()};counts={k:len(v) for k,v in ids.items()}
        tp,fp,fn,tn=(counts[k] for k in ['TP','FP','FN','TN'])
        recall=ratio(tp,tp+fn);fpr=ratio(fp,fp+tn);precision=ratio(tp,tp+fp)
        roc={'x_fraction':fpr['fraction'],'y_fraction':recall['fraction'],'x':fpr['value'],'y':recall['value']} if fpr['value'] is not None and recall['value'] is not None else None
        pr={'x_fraction':recall['fraction'],'y_fraction':precision['fraction'],'x':recall['value'],'y':precision['value']} if recall['value'] is not None and precision['value'] is not None else None
        states.append({'ordinal':ordinal,
                       'threshold':{'kind':'above-maximum' if boundary is None else 'at-score','value':canonical(boundary) if boundary is not None else None,'above_score':canonical(boundaries[0]) if boundary is None else None},
                       'rule':'mathematical all-negative endpoint' if boundary is None else 'score >= threshold',
                       'positive_ids':sorted(predicted),'added_ids':sorted(predicted-prior),'removed_ids':sorted(prior-predicted),'prior_is_subset':prior<=predicted,
                       'ids':ids,'counts':counts,'metrics':{'recall':recall,'fpr':fpr,'precision':precision},
                       'roc':roc,'roc_status':'defined' if roc is not None else 'undefined-denominator',
                       'pr':pr,'pr_status':'defined' if pr is not None else 'undefined-denominator'})
        prior=predicted
    return {'samples':[{'id':s['id'],'label':s['label'],'score':canonical(s['score'])} for s in samples],
            'sample_count':len(samples),'actual_positive_count':sum(s['label'] for s in samples),'actual_negative_count':sum(1-s['label'] for s in samples),
            'unique_score_count':len(boundaries),'states':states}
