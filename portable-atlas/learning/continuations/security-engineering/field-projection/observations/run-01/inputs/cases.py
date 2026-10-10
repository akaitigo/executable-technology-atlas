"""Atlas: enumerate the contracted finite requests, without expected outcomes."""
from copy import deepcopy


def all_cases(fixture):
    cases = []
    def add(key, group, label, role='viewer', request=None, context=None, variant=None):
        cases.append({'id': key, 'group': group, 'label': label,
                      'context': deepcopy(fixture['contexts'][role] if context is None else context),
                      'request': deepcopy(request or {'object_id': 'red-report', 'operation': 'read'}),
                      'storeVariant': variant})
    for role in fixture['roles']:
        for obj in fixture['records']:
            add(role+'/'+obj, 'object', role+' / '+obj+' / 指定省略', role,
                {'object_id': obj, 'operation': 'read'})
    for role in fixture['roles']:
        for field in fixture['fields']:
            add(role+'/field/'+field, 'field', role+' / '+field+'だけ要求', role,
                {'object_id': 'red-report', 'operation': 'read', 'fields': [field]})
    base = {'object_id': 'red-report', 'operation': 'read'}
    unknown_context = deepcopy(fixture['contexts']['viewer']); unknown_context['role'] = 'unknown'
    add('unknown-role', 'boundary', '信頼済みcontextの不明role', context=unknown_context)
    for key,label,changes in [
        ('role-override','利用者入力でroleを追加',{'role':'auditor'}),
        ('unknown-field','存在しない項目を要求',{'fields':['not_a_field']}),
        ('tenant-override','利用者入力でtenantを追加',{'tenant_id':'tenant-blue'}),
        ('fields-string','項目一覧を文字列で送る',{'fields':'id'}),
        ('empty-fields','空の項目一覧',{'fields':[]}),
        ('duplicate-fields','同じ項目を重複要求',{'fields':['id','id']}),
        ('unknown-object','存在しないレコード',{'object_id':'missing'}),
        ('write-operation','未対応の書込操作',{'operation':'write'}),
    ]: add(key,'boundary',label,request={**base,**changes})
    add('missing-object','boundary','object_idを省略',request={'operation':'read'})
    add('no-context','boundary','上流contextなし'); cases[-1]['context']=None
    add('mixed-forbidden','boundary','許可idと禁止internal_noteを同時要求',request={**base,'fields':['id','internal_note']})
    add('future-field','future','storeに将来の内部項目を追加',variant={'future_internal':'架空の将来追加項目'})
    return cases
