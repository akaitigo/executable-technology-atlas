"""Independent expected lifecycle: POSIX table, no execution-code import or simulated result."""
EXPECTED={
 'close':{'timeout':False,'eof':True,'exit':0,'open_writers_at_checkpoint':0},
 'leak-release':{'timeout':True,'eof':True,'exit':0,'open_writers_at_checkpoint':1},
 'leak-signal':{'timeout':True,'eof':False,'exit':-15,'open_writers_at_checkpoint':1},
}
def check(result):
    spec=result['input'];expected=EXPECTED[spec['mode']]
    pe=result['parent_events'];ce=result['child_events']
    names=[e['event'] for e in pe]; cn=[e['event'] for e in ce]
    def get(name): return next(e for e in pe if e['event']==name)
    assert result['status']=='observed' and result['failure'] is None
    assert result['parent_pid']!=result['child_pid']
    assert ce[0]['event']=='ready' and ce[0]['pid']==result['child_pid'] and ce[0]['ppid']==result['parent_pid']
    assert ce[0]['write_end_inherited'] is False and ce[0]['sigterm_default'] is True
    assert result['bounded_timeout']==expected['timeout']
    assert ('eof' in cn)==expected['eof']
    assert result['returncode']==expected['exit']
    assert get('writer_refs_checkpoint')['parent_write_refs']==expected['open_writers_at_checkpoint']
    assert get('writer_refs_checkpoint')['child_write_refs']==0
    assert names.index('ready_received')<names.index('original_write_closed')<names.index('writer_refs_checkpoint')
    payload=bytes.fromhex(''.join(e['hex'] for e in ce if e['event']=='data'))
    assert payload==spec['payload'].encode('ascii')
    if expected['timeout']:
        t=get('bounded_timeout')
        assert t['child_alive'] and t['parent_write_refs']==1
        assert t['elapsed_ns']>=spec['timeout_ms']*1000000
        action='leak_write_closed' if spec['mode']=='leak-release' else 'sigterm_sent'
        assert names.index('bounded_timeout')<names.index(action)<names.index('cleanup_complete')
    if expected['eof']:
        eof=next(e for e in ce if e['event']=='eof')
        assert eof['read_return_bytes']==0 and cn[-1]=='read_end_closed'
        assert cn.index('ready')<cn.index('eof')<cn.index('read_end_closed')
        # Do not compare different process monotonic clocks on macOS Python 3.9.
    if spec['mode']=='leak-signal':
        assert get('sigterm_sent')['child_pid']==result['child_pid'] and get('sigterm_sent')['signal']==15
    assert result['raw_child_stderr']==''
    assert result['cleanup']['parent_open_fds']==0 and result['cleanup']['child_reaped'] and result['cleanup']['streams_closed']
    assert result['cleanup']['fallback']==[]
    assert [e['seq'] for e in pe]==list(range(len(pe)))
    for stream in (pe,ce): assert all(a['mono_ns']<=b['mono_ns'] for a,b in zip(stream,stream[1:]))
    return dict(expected,received_bytes=len(payload),parent_child_distinct=True,cleanup='all owned FD/child streams closed and child reaped')
