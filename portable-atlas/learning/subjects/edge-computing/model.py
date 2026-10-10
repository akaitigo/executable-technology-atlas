"""Finite two-node offline synchronization model; no network or edge hardware."""
import copy
import hashlib
import json
from datetime import datetime, timezone


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

def dominates(a, b):
    return all(x >= y for x,y in zip(a,b)) and any(x > y for x,y in zip(a,b))

class Model:
    def __init__(self, config):
        self.config=config
        self.nodes={name:{'online':True,'clock':[0,0],'heads':[],'seen':{},'outbox':[]} for name in ('A','B')}
        self.events={}
        self.raw=[]
        self.counts={'accepted':0,'rejected':0,'delivered':0,'duplicate':0,'conflict':0}
        self.cost=config['cost_model']
        self.valid=type(config.get('limit')) is int and 1<=config['limit']<=8 and config.get('policy') in ('logical','wallclock') and config.get('placement') in ('edge','central')

    def log(self, step, action, disposition, **extras):
        self.raw.append({'at':datetime.now(timezone.utc).isoformat(),'step':step,'action':action,'disposition':disposition,**extras,'state':copy.deepcopy(self.nodes),'counts':dict(self.counts)})

    def merge(self,node,event):
        heads=node['heads']
        if self.config['policy']=='wallclock':
            node['heads']=copy.deepcopy([max(heads+[event],key=lambda x:(x['wall_ms'],x['id']))])
        else:
            if not any(dominates(x['version'],event['version']) for x in heads):
                heads=[x for x in heads if not dominates(event['version'],x['version'])]
                heads.append(copy.deepcopy(event))
                node['heads']=sorted(heads,key=lambda x:x['id'])
        node['clock']=[max(x,y) for x,y in zip(node['clock'],event['version'])]
        node['seen'][event['id']]=hashlib.sha256(canonical(event).encode()).hexdigest()

    def execute(self,operations):
        if not self.valid:
            self.log(0,{'op':'validate'},'invalid-config')
            return self.result()
        for step, action in enumerate(operations,1):
            op=action['op']
            if op=='disconnect' or op=='reconnect':
                for node in self.nodes.values(): node['online']=op=='reconnect'
                self.log(step,action,op)
            elif op=='edit':
                name=action['node']; node=self.nodes[name]
                value=action['value']; wall=action['wall_ms']
                if type(value) is not int or not -100<=value<=100 or type(wall) is not int:
                    self.counts['rejected']+=1; self.log(step,action,'invalid-input'); continue
                if self.config['placement']=='central' and not node['online']:
                    self.counts['rejected']+=1; self.log(step,action,'central-offline-blocked',modeled_ms=None); continue
                if len(node['outbox'])>=self.config['limit']:
                    self.counts['rejected']+=1; self.log(step,action,'buffer-full-rejected',modeled_ms=None); continue
                index=0 if name=='A' else 1
                version=list(node['clock']); version[index]+=1
                event={'id':f'{name}{version[index]}','origin':name,'value':value,'version':version,'wall_ms':wall}
                self.events[event['id']]=copy.deepcopy(event)
                self.merge(node,event); node['outbox'].append(event['id']); self.counts['accepted']+=1
                # Entirely supplied cost model. Runtime wall time is not a network measurement.
                cost=self.cost['edge_edit_ms'] if self.config['placement']=='edge' else self.cost['remote_rtt_ms']+self.cost['remote_compute_ms']
                self.log(step,action,'local-accepted',event=event,modeled_ms=cost)
            elif op=='deliver':
                event=copy.deepcopy(self.events[action['id']]); source=event['origin']; target='B' if source=='A' else 'A'; node=self.nodes[target]
                if 'tamper_value' in action: event['value']=action['tamper_value']
                if not node['online'] or not self.nodes[source]['online']:
                    self.log(step,action,'offline-retained',modeled_ms=None); continue
                fingerprint=hashlib.sha256(canonical(event).encode()).hexdigest()
                if event['id'] in node['seen']:
                    if node['seen'][event['id']]!=fingerprint:
                        self.counts['conflict']+=1; self.log(step,action,'same-id-conflict-held',event=event,modeled_ms=self.cost['remote_rtt_ms']+self.cost['remote_compute_ms']); continue
                    self.counts['duplicate']+=1; disposition='duplicate-no-change'
                else:
                    self.merge(node,event); self.counts['delivered']+=1; disposition='applied'
                queue=self.nodes[source]['outbox']
                if event['id'] in queue: queue.remove(event['id'])
                self.log(step,action,disposition,event=event,target=target,modeled_ms=self.cost['remote_rtt_ms']+self.cost['remote_compute_ms'])
            else:
                raise ValueError('unsupported operation')
        return self.result()

    def result(self):
        return {'config_valid':self.valid,'state':copy.deepcopy(self.nodes),'events':copy.deepcopy(self.events),'counts':dict(self.counts),
                'modeled_ms':sum(x.get('modeled_ms') or 0 for x in self.raw),'raw':self.raw,'scope':'deterministic two-node cost/sync model; no network/hardware latency measured'}
