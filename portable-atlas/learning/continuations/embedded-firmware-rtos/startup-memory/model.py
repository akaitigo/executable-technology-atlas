"""Atlas: finite byte startup model; no CPU, linker, device or host memory access."""
import copy

ROM = [208,209,210,211,17,34,51,68,232,233,234,235,236,237,238,239]
RAM = [165,165,165,165,165,165,204,165,165,165,165,165,204,165,165,165]
SPECS = [
    ('copy-zero-main', ['copy','zero','main'],4,4,False),
    ('zero-copy-main', ['zero','copy','main'],4,4,False),
    ('skip-copy', ['zero','main'],4,4,False),
    ('skip-zero', ['copy','main'],4,4,False),
    ('main-early', ['main','copy','zero'],4,4,False),
    ('copy-one-past', ['copy','zero','main'],4,4,True),
    ('empty-regions', ['copy','zero','main'],0,0,False),
]

def require(condition, reason):
    if not condition:
        raise ValueError(reason)

def validate(fixture, case_id):
    require(type(fixture) is dict and set(fixture)=={
        'schema','rom_base','ram_base','size','rom','ram_initial',
        'data_source_offset','data_target_offset','bss_offset','guard_offsets','cases'}, 'SCHEMA')
    for name in ['schema','rom_base','ram_base','size','data_source_offset','data_target_offset','bss_offset']:
        require(type(fixture[name]) is int, 'INTEGER_REQUIRED')
    require(fixture['schema']==1 and fixture['size']==16, 'FIXED_MAP')
    for name in ['rom','ram_initial']:
        require(type(fixture[name]) is list and len(fixture[name])==16 and
                all(type(x) is int and 0<=x<=255 for x in fixture[name]), 'MEMORY_BYTES')
    guards=fixture['guard_offsets']
    require(type(guards) is list and len(guards)==2 and all(type(x) is int and 0<=x<16 for x in guards) and len(set(guards))==2, 'GUARD_RANGE')
    require(type(fixture['cases']) is list and len(fixture['cases'])==7, 'CASE_SCHEMA')
    for c,spec in zip(fixture['cases'],SPECS):
        require(type(c) is dict and set(c)=={'id','operations','data_length','bss_length','copy_one_past'}, 'CASE_SCHEMA')
        require(type(c['data_length']) is int and type(c['bss_length']) is int, 'INTEGER_REQUIRED')
        dl,bl=c['data_length'],c['bss_length'];ds=fixture['data_source_offset'];dt=fixture['data_target_offset'];bs=fixture['bss_offset']
        require(0<=dl<=16 and 0<=bl<=16 and 0<=ds<=16 and 0<=dt<=16 and 0<=bs<=16 and ds+dl<=16 and dt+dl<=16 and bs+bl<=16, 'MAP_RANGE')
        dr=set(range(dt,dt+dl));br=set(range(bs,bs+bl))
        require(not dr.intersection(br), 'OVERLAP')
        require(not set(guards).intersection(dr|br), 'GUARD_RANGE')
        name,ops,expected_dl,expected_bl,past=spec
        require(type(c['copy_one_past']) is bool and type(c['operations']) is list and
                c['id']==name and c['operations']==ops and dl==expected_dl and bl==expected_bl and c['copy_one_past'] is past, 'CASE_SCHEMA')
    require(fixture['rom']==ROM and fixture['ram_initial']==RAM, 'FIXED_MEMORY')
    require((fixture['rom_base'],fixture['ram_base'],fixture['data_source_offset'],fixture['data_target_offset'],fixture['bss_offset'],guards)==(4096,8192,4,2,8,[6,12]), 'FIXED_MAP')
    require(type(case_id) is str and case_id in [x[0] for x in SPECS], 'UNKNOWN_CASE')
    return next(c for c in fixture['cases'] if c['id']==case_id)

def execute(fixture, case_id):
    case=validate(fixture,case_id)  # All input refusal happens before mutable model memory or writes.
    rom=list(fixture['rom']);ram=list(fixture['ram_initial']);writes=[];snapshots=[]
    copied=False;zeroed=False;main=None
    ds,dt,bs=fixture['data_source_offset'],fixture['data_target_offset'],fixture['bss_offset']
    dl,bl=case['data_length'],case['bss_length'];guards=fixture['guard_offsets']
    def intact():
        return all(ram[n]==fixture['ram_initial'][n] for n in guards)
    def snapshot(phase):
        snapshots.append({'phase':phase,'ram':list(ram),'copy_completed':copied,'zero_completed':zeroed})
    def write(phase,target,value,source=None):
        writes.append({'phase':phase,'ram_offset':target,'rom_offset':source,'before':ram[target],'after':value})
        ram[target]=value
    snapshot('initial')
    for phase in case['operations']:
        if phase=='copy':
            for offset in range(dl+int(case['copy_one_past'])):
                write('copy',dt+offset,rom[ds+offset],ds+offset)
            copied=True
        elif phase=='zero':
            for offset in range(bl):
                write('zero',bs+offset,0)
            zeroed=True
        else:
            data=list(ram[dt:dt+dl]);bss=list(ram[bs:bs+bl]);values=data==rom[ds:ds+dl] and bss==[0]*bl
            main={'data':data,'bss':bss,'copy_completed':copied,'zero_completed':zeroed,
                  'guards_intact':intact(),'values_expected':values,'initialized':copied and zeroed and intact() and values}
        snapshot(phase)
    valid_writes=all((dt<=w['ram_offset']<dt+dl) if w['phase']=='copy' else (bs<=w['ram_offset']<bs+bl) for w in writes)
    return {'id':case_id,'classification':'NORMAL' if main['initialized'] and valid_writes else 'INTENTIONAL_FAULT',
            'writes':writes,'snapshots':snapshots,'main':main,'final_ram':ram,'final_rom':rom,
            'rom_unchanged':rom==fixture['rom'],'guards_intact':intact(),'write_ranges_valid':valid_writes,'write_count':len(writes)}
