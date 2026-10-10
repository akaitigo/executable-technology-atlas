"""Independent event/order/time/binding rules; does not import runner."""
import collections,re
EXPECTED={
 'success':([200],[200],[],0),
 'error':([503],[None],[],0),
 'missing-propagation':([200],[200],[],1),
 'error-orphan':([503],[None],[],1),
 'batch':([200,503,200],[100,None,300],[],1),
 'upper-bound':([200],[300],[],0),
 'zero-units':([],[],['invalid-units'],0),
 'unexpected-key':([],[],['unexpected-label-key'],0),
 'unexpected-value':([],[],['unexpected-label-value'],0)
}
def audit(raw):
    statuses,amounts,reasons,orphans=EXPECTED[raw['case']]
    assert [r['status'] for r in raw['responses']]==statuses,'responses'
    assert [r.get('amount') for r in raw['responses']]==amounts,'amounts'
    assert [r['reason'] for r in raw['rejected']]==reasons,'rejection'
    logs=raw['logs'];spans=raw['spans'];assert len(logs)==6*len(statuses) and len(spans)==2*len(statuses),'counts'
    assert [r['sequence'] for r in logs]==list(range(1,len(logs)+1)),'sequence'
    times=[r['monotonic_ns'] for r in logs];assert times==sorted(times),'monotonic-order'
    ids={r['span_id']:r for r in spans};assert len(ids)==len(spans),'span-unique'
    found=[];expected_metrics=collections.Counter()
    for i,response in enumerate(raw['responses']):
        status=response['status'];chunk=logs[i*6:(i+1)*6]
        assert [x['event'] for x in chunk]==['request.begin','lookup.begin','lookup.result' if status==200 else 'lookup.error','lookup.end','request.response','request.end'],'event-order'
        root=ids[chunk[0]['span_id']];child=ids[chunk[1]['span_id']]
        assert root['name']=='request' and child['name']=='price_lookup','span-names'
        assert root['parent_span_id'] is None,'root-parent'
        assert root['start_ns']<=child['start_ns']<=child['end_ns']<=root['end_ns'],'duration-containment'
        assert root['status']==child['status']==('OK' if status==200 else 'ERROR'),'span-status'
        if child['parent_span_id']!=root['span_id'] or child['trace_id']!=root['trace_id']:
            found.append({'kind':'orphan-span','span_id':child['span_id'],'actual_parent':child['parent_span_id'],'root_span_id':root['span_id'],'child_trace':child['trace_id'],'request_trace':root['trace_id']})
        for row in chunk:
            bound=ids[row['span_id']];assert row['trace_id']==bound['trace_id'],'log-span-binding'
            assert bound['start_ns']<=row['monotonic_ns']<=bound['end_ns'],'log-duration-binding'
            assert re.fullmatch('[0-9a-f]{32}',row['trace_id']) and re.fullmatch('[0-9a-f]{16}',row['span_id']),'ids'
        assert chunk[4]['attributes']['status']==status,'response-log'
        if status==503:assert chunk[2]['severity']=='ERROR' and chunk[2]['attributes']['error_type']=='LookupError','error-log'
        expected_metrics[('quote','success' if status==200 else 'error')]+=1
    for span in spans:
        assert type(span['duration_ns']) is int and span['end_ns']>=span['start_ns'] and span['duration_ns']==span['end_ns']-span['start_ns'],'duration'
    actual_metrics={}
    for m in raw['metrics']:
        assert m['name']=='requests_total' and set(m['labels'])=={'route','outcome'},'metric-labels'
        key=(m['labels']['route'],m['labels']['outcome']);assert key not in actual_metrics,'metric-duplicate';actual_metrics[key]=m['value']
    assert actual_metrics==dict(expected_metrics),'metric-counts'
    assert len(found)==orphans,'orphan-count'
    return {'validScenario':True,'bindingComplete':not found,'findings':found,'requests':len(statuses),'logs':len(logs),'spans':len(spans),'metricSeries':len(raw['metrics']),'durationChecks':'monotonic + containment + arithmetic, exact timings not fixed'}
