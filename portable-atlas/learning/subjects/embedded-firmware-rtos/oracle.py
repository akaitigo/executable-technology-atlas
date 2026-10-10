"""Independent literal interleavings and symbolic last-writer/interval oracle."""
# All binomial(4,2)=6 orderings preserve each actor's read-before-write.
ALL=[['MR','MW','IR','IW'],['MR','IR','MW','IW'],['MR','IR','IW','MW'],['IR','MR','MW','IW'],['IR','MR','IW','MW'],['IR','IW','MR','MW']]
LEGAL=[['MR','MW','IR','IW'],['MR','IR','IW','MW'],['IR','IW','MR','MW']]
HAND={'main-first':{'naive':2,'critical':2},'preempt-main':{'naive':1,'critical':2},'isr-first':{'naive':2,'critical':2}}
def counter_expected(order,mode):
    if order not in LEGAL:raise ValueError('unsupported ISR preemption')
    if mode=='critical':return 2
    # Symbolic assignments, independently count writes visible at each read.
    final_actor=order[-1][0];read_index=order.index(final_actor+'R');other='I' if final_actor=='M' else 'M'
    return 2 if order.index(other+'W')<read_index else 1

def latency_expected(mode,hold,arrival,deadline):
    # Enumerate masked tick set, no max/start formula copied from model.
    blocked=set(range(hold)) if mode=='critical' else set()
    service_tick=arrival
    while service_tick in blocked:service_tick+=1
    response=(service_tick-arrival)+1
    return {'wait':service_tick-arrival,'response':response,'meetsDeadline':response<=deadline}
