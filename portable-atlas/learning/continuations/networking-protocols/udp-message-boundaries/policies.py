"""Offline interpretations of actual recv results; never open sockets."""
def compare(events):
    received=[event['payload_hex'] for event in events if event['kind']=='recvfrom-return']
    tcp_eof=[]
    for payload in received:
        if payload=='':
            break
        tcp_eof.append(payload)
    # A deliberately wrong prototype borrows stream buffering, including NEXT.
    stream_buffer=''.join(received)
    return {'scope':'offline faulty consumer prototypes on actual API returns',
            'datagram_candidates':received,
            'tcp_eof_fault':tcp_eof,
            'stream_join_fault':stream_buffer,
            'warning':'Candidates are not validated business messages. recvfrom alone has no returned truncation flag; source identity is not authentication.'}
