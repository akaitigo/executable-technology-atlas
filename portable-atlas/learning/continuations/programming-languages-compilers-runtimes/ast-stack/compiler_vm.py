"""Atlas: bounded AST lowering and a separate structured-instruction stack machine."""
LIMIT = 64

def compile_tree(tree):
    constants, code, origins, mapping, seen = [], [], [], [], set()
    def emit(instruction, node):
        if len(code) >= LIMIT:
            raise ValueError('instruction limit')
        pc = len(code)
        code.append(instruction)
        origins.append({'pc': pc, 'node_id': node['id'], 'span': list(node['span'])})
        return pc
    def walk(node, depth=0):
        if depth > 32 or len(seen) >= LIMIT or not isinstance(node, dict):
            raise ValueError('AST resource or shape boundary')
        ident, kind = node['id'], node['kind']
        if not isinstance(ident, str) or ident in seen:
            raise ValueError('AST ids must be unique strings')
        seen.add(ident)
        start, emitted = len(code), None
        if kind == 'Integer':
            value = node['value']
            if type(value) is not int or not 0 <= value <= 999999:
                raise ValueError('bounded integer literal required')
            if value not in constants:
                constants.append(value)
            emitted = emit(['CONST', constants.index(value)], node)
        elif kind == 'Group':
            walk(node['child'], depth + 1)
        elif kind in ('Add', 'Multiply'):
            walk(node['left'], depth + 1)
            walk(node['right'], depth + 1)
            emitted = emit(['ADD' if kind == 'Add' else 'MUL'], node)
        else:
            raise ValueError('unsupported AST kind: ' + str(kind))
        mapping.append({'node_id': ident, 'kind': kind, 'span': list(node['span']),
                        'instruction_range': [start, len(code)], 'emitted_pc': emitted})
    walk(tree)
    return {'constants': constants, 'code': code, 'origins': origins, 'node_mapping': mapping,
            'pc_unit': 'zero-based instruction ordinal, not byte offset'}

def execute_vm(constants, code):
    """No AST access and no tree-evaluator call. Rejection preserves the current stack."""
    stack, trace = [], []
    max_height = 0
    def reject(diagnostic, pc, instruction=None, phase='instruction'):
        before = list(stack)
        trace.append({'pc': pc, 'instruction': instruction, 'before': before, 'after': list(stack),
                      'height_before': len(stack), 'height_after': len(stack), 'status': 'rejected',
                      'operands': None, 'constant_index': None, 'constant_value': None,
                      'diagnostic': diagnostic, 'phase': phase})
        return {'status': 'rejected', 'value': None, 'final_stack': list(stack), 'trace': trace,
                'diagnostic': {'code': diagnostic, 'pc': pc, 'phase': phase},
                'executed_instructions': sum(t['status'] == 'executed' for t in trace), 'max_height': max_height}
    if type(constants) is not list or len(constants) > LIMIT or any(type(x) is not int or not 0 <= x <= 999999 for x in constants):
        return reject('INVALID_CONSTANT_TABLE', None, phase='program')
    if type(code) is not list or len(code) > LIMIT:
        return reject('INVALID_CODE', None, phase='program')
    for pc, instruction in enumerate(code):
        if type(instruction) is not list or not instruction or type(instruction[0]) is not str:
            return reject('INVALID_INSTRUCTION', pc, instruction)
        op = instruction[0]
        if op not in ('CONST', 'ADD', 'MUL'):
            return reject('UNKNOWN_OPCODE', pc, instruction)
        if len(instruction) != (2 if op == 'CONST' else 1):
            return reject('INVALID_INSTRUCTION', pc, instruction)
        before, operands, index, literal = list(stack), None, None, None
        if op == 'CONST':
            index = instruction[1]
            if type(index) is not int or not 0 <= index < len(constants):
                return reject('INVALID_CONSTANT_INDEX', pc, instruction)
            if len(stack) >= LIMIT:
                return reject('STACK_LIMIT', pc, instruction)
            literal = constants[index]
            stack.append(literal)
        else:
            if len(stack) < 2:
                return reject('STACK_UNDERFLOW', pc, instruction)
            right, left = stack.pop(), stack.pop()
            operands = {'left': left, 'right': right}
            stack.append(left + right if op == 'ADD' else left * right)
        max_height = max(max_height, len(stack))
        trace.append({'pc': pc, 'instruction': list(instruction), 'before': before, 'after': list(stack),
                      'height_before': len(before), 'height_after': len(stack), 'status': 'executed',
                      'operands': operands, 'constant_index': index, 'constant_value': literal,
                      'diagnostic': None, 'phase': 'instruction'})
    if len(stack) != 1:
        return reject('FINAL_STACK_SHAPE', len(code), phase='finish')
    return {'status': 'returned', 'value': stack[0], 'final_stack': list(stack), 'trace': trace,
            'diagnostic': None, 'executed_instructions': len(code), 'max_height': max_height}
