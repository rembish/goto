from opcode import opname, HAVE_ARGUMENT, opmap
from sys import version_info
from types import CodeType, FunctionType

__all__ = ["goto"]

IS_PY3 = version_info[0] == 3


class MissingLabelError(ValueError):
    pass


class ExistingLabelError(ValueError):
    pass


def goto(function):
    def translate(optcode):
        if IS_PY3:
            return optcode
        return ord(optcode)

    if IS_PY3:
        code = function.__code__
    else:
        code = function.func_code

    labels = {}
    gotos = []
    command = ''
    previous = ''
    i = 0

    while i < len(code.co_code):
        opcode = translate(code.co_code[i])
        operation = opname[opcode]

        if opcode >= HAVE_ARGUMENT:
            lo_byte = translate(code.co_code[i + 1])
            hi_byte = translate(code.co_code[i + 2])
            argument_position = (hi_byte << 8) ^ lo_byte

            if operation == 'LOAD_GLOBAL':
                command = code.co_names[argument_position]

            if operation == 'LOAD_ATTR' and previous == 'LOAD_GLOBAL':
                if command == 'label':
                    label = code.co_names[argument_position]
                    if label in labels:
                        raise ExistingLabelError(
                            'Label redifinition: {0}'.format(label))

                    labels.update({label: i - 3})

                elif command == 'goto':
                    gotos += [(code.co_names[argument_position], i - 3)]

            i += 2

        previous = operation
        i += 1

    codebytes_list = list(code.co_code)
    if IS_PY3:
        codebytes_list = list(map(chr, codebytes_list))

    nop = chr(opmap['NOP'])
    for index in labels.values():
        codebytes_list[index: index + 7] = [nop] * 7

    jump = chr(opmap['JUMP_ABSOLUTE'])
    for label, index in gotos:
        if label not in labels:
            raise MissingLabelError('Missing label: {0}'.format(label))

        target_index = labels[label] + 7
        codebytes_list[index] = jump
        codebytes_list[index + 1] = chr(target_index & 0xFF)
        codebytes_list[index + 2] = chr((target_index >> 8) & 0xFF)

    if IS_PY3:
        code = CodeType(
            code.co_argcount, code.co_kwonlyargcount,
            code.co_nlocals, code.co_stacksize, code.co_flags,
            bytes(map(ord, codebytes_list)), code.co_consts,
            code.co_names, code.co_varnames,
            code.co_filename, code.co_name, code.co_firstlineno,
            code.co_lnotab)
        rewritten = FunctionType(code, function.__globals__)

    else:
        code = CodeType(
            code.co_argcount, code.co_nlocals, code.co_stacksize,
            code.co_flags,
            "".join(codebytes_list), code.co_consts,
            code.co_names, code.co_varnames,
            code.co_filename, code.co_name, code.co_firstlineno,
            code.co_lnotab)
        rewritten = FunctionType(code, function.func_globals)

    return rewritten
