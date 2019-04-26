#!/usr/bin/python3

from hashlib import sha1
import re
import solcx

from brownie.exceptions import CompilerError
import brownie._config
CONFIG = brownie._config.CONFIG

STANDARD_JSON = {
    'language': "Solidity",
    'sources': {},
    'settings': {
        'outputSelection': {'*': {
            '*': [
                "abi",
                "evm.assembly",
                "evm.bytecode",
                "evm.deployedBytecode"
            ],
            '': ["ast"]
        }},
        "optimizer": {
            "enabled": CONFIG['solc']['optimize'],
            "runs": CONFIG['solc']['runs']
        }
    }
}

_sources = {}


def set_solc_version():
    solcx.set_solc_version(CONFIG['solc']['version'])
    CONFIG['solc']['version'] = solcx.get_solc_version_string().strip('\n')


def get_inheritance_map(contract_files):
    inheritance_map = {}
    for filename in contract_files:
        code = filename.open().read()
        for name in (
            re.findall(
                "\n(?:contract|library|interface) (.*?){", code, re.DOTALL)
        ):
            names = [i.strip(',') for i in name.strip().split(' ')]
            if names[0] in inheritance_map:
                raise ValueError("Multiple contracts named {}".format(names[0]))
            inheritance_map[names[0]] = set(names[2:])
    for i in range(len(inheritance_map)):
        for base, inherited in [
            (k, x) for k, v in inheritance_map.copy().items() if v for x in v
        ]:
            inheritance_map[base] |= inheritance_map[inherited]
    return inheritance_map


def compile_contracts(contract_files):
    '''Compiles the contract files and returns a dict of compiler outputs.'''
    CONFIG['solc']['version'] = solcx.get_solc_version_string().strip('\n')
    print("Compiling contracts...")
    print("Optimizer: {}".format(
        "Enabled  Runs: "+str(CONFIG['solc']['runs']) if
        CONFIG['solc']['optimize'] else "Disabled"
    ))
    print("\n".join(" - {}...".format(i.name) for i in contract_files))
    input_json = STANDARD_JSON.copy()
    input_json['sources'] = dict((
        str(i),
        {'content': i.open().read()}
    ) for i in contract_files)
    return _compile_and_format(input_json)


def compile_source(source):
    input_json = STANDARD_JSON.copy()
    input_json['sources'] = {"<string>": {'content': source}}
    return _compile_and_format(input_json)


def _compile_and_format(input_json):
    try:
        compiled = solcx.compile_standard(
            input_json,
            optimize=CONFIG['solc']['optimize'],
            optimize_runs=CONFIG['solc']['runs'],
            allow_paths="."
        )
    except solcx.exceptions.SolcError as e:
        raise CompilerError(e)
    compiled = _generate_pcMap(compiled)
    result = {}
    compiler_info = CONFIG['solc'].copy()
    compiler_info['version'] = solcx.get_solc_version_string().strip('\n')
    for filename in input_json['sources']:
        for match in re.findall(
            "\n(?:contract|library|interface) [^ {]{1,}",
            input_json['sources'][filename]['content']
        ):
            type_, name = match.strip('\n').split(' ')
            data = compiled['contracts'][filename][name]
            evm = data['evm']
            ref = [
                (k, x) for v in evm['bytecode']['linkReferences'].values()
                for k, x in v.items()
            ]
            # standardize unlinked library tags
            for n, loc in [(i[0], x['start']*2) for i in ref for x in i[1]]:
                evm['bytecode']['object'] = "{}__{:_<36}__{}".format(
                    evm['bytecode']['object'][:loc],
                    n[:36],
                    evm['bytecode']['object'][loc+40:]
                )
            result[name] = {
                'abi': data['abi'],
                'ast': compiled['sources'][filename]['ast'],
                'bytecode': evm['bytecode']['object'],
                'compiler': compiler_info,
                'contractName': name,
                'deployedBytecode': evm['deployedBytecode']['object'],
                'deployedSourceMap': evm['deployedBytecode']['sourceMap'],
                'networks': {},
                'opcodes': evm['deployedBytecode']['opcodes'],
                'sha1': sha1(input_json['sources'][filename]['content'].encode()).hexdigest(),
                'source': input_json['sources'][filename]['content'],
                'sourceMap': evm['bytecode']['sourceMap'],
                'sourcePath': filename,
                'type': type_,
                'pcMap': evm['pcMap'],
                'allSourcePaths': sorted(set(
                    i['contract'] for i in evm['pcMap'] if i['contract']
                ))
            }
            result[name]['coverageMap'] = _generate_coverageMap(result[name])
    return result


def _generate_pcMap(compiled):
    '''
    Generates an expanded sourceMap useful for debugging.
    [{
        'contract': relative path of the contract source code
        'jump': jump instruction as supplied in the sourceMap (-,i,o)
        'op': opcode string
        'pc': program counter as given by debug_traceTransaction
        'start': source code start offset
        'stop': source code stop offset
        'value': value of the instruction, if any
    }, ... ]
    '''
    id_map = dict((v['id'], k) for k, v in compiled['sources'].items())
    for filename, name in [(k, x) for k, v in compiled['contracts'].items() for x in v]:
        bytecode = compiled['contracts'][filename][name]['evm']['deployedBytecode']

        if not bytecode['object']:
            compiled['contracts'][filename][name]['evm']['pcMap'] = []
            continue
        pcMap = []
        opcodes = bytecode['opcodes']
        source_map = bytecode['sourceMap']
        while True:
            try:
                i = opcodes[:-1].rindex(' STOP')
            except ValueError:
                break
            if 'JUMPDEST' in opcodes[i:]:
                break
            opcodes = opcodes[:i+5]
        opcodes = opcodes.split(" ")[::-1]
        pc = 0
        last = source_map.split(';')[0].split(':')
        for i in range(3):
            last[i] = int(last[i])
        pcMap.append({
            'start': last[0],
            'stop': last[0]+last[1],
            'op': opcodes.pop(),
            'contract': id_map[last[2]],
            'jump': last[3],
            'pc': 0
        })
        pcMap[0]['value'] = opcodes.pop()
        for value in source_map.split(';')[1:]:
            pc += 1
            if pcMap[-1]['op'][:4] == "PUSH":
                pc += int(pcMap[-1]['op'][4:])
            if value:
                value = (value+":::").split(':')[:4]
                for i in range(3):
                    value[i] = int(value[i] or last[i])
                value[3] = value[3] or last[3]
                last = value
            pcMap.append({
                'start': last[0],
                'stop': last[0]+last[1],
                'op': opcodes.pop(),
                'contract': id_map[last[2]] if last[2] != -1 else False,
                'jump': last[3],
                'pc': pc
            })
            if opcodes[-1][:2] == "0x":
                pcMap[-1]['value'] = opcodes.pop()
        compiled['contracts'][filename][name]['evm']['pcMap'] = pcMap
    return compiled


def _generate_coverageMap(build):
    """Given the compiled project as supplied by compiler.compile_contracts(),
    returns the function and line based coverage maps for unit test coverage
    evaluation.

    A coverage map item is structured as follows:

    {
        "/path/to/contract/file.sol":{
            "functionName":{
                "fn": {},
                "line":[{},{},{}]
            }
        }
    }

    Each dict in fn/line is as follows:

    {
        'start': source code start offset
        'stop': source code stop offset
        'pc': set of opcode program counters tied to the map item
        'jump': pc of the JUMPI instruction, if it is a jump
        'tx': empty set, used to record transactions that hit the item
    }

    Items relating to jumps also include keys 'true' and 'false', which are
    also empty sets used in the same way as 'tx'"""

    fn_map = dict((x, {}) for x in build['allSourcePaths'])

    for i in _isolate_functions(build):
        fn_map[i.pop('contract')][i.pop('method')] = {'fn': i, 'line': []}
    line_map = _isolate_lines(build)
    if not line_map:
        return {}

    # future me - i'm sorry for this line
    for source, fn_name, fn in [(k, x, v[x]['fn']) for k, v in fn_map.items() for x in v]:
        for ln in [
            i for i in line_map if i['contract'] == source and
            i['start'] == fn['start'] and i['stop'] == fn['stop']
        ]:
            # remove duplicate mappings
            line_map.remove(ln)
        for ln in [
            i for i in line_map if i['contract'] == source and
            i['start'] >= fn['start'] and i['stop'] <= fn['stop']
        ]:
            # apply method names to line mappings
            line_map.remove(ln)
            fn_map[ln.pop('contract')][fn_name]['line'].append(ln)
        fn_map[source][fn_name]['total'] = sum([1 if not i['jump'] else 2 for i in fn_map[source][fn_name]['line']])
    return fn_map


def _isolate_functions(compiled):
    '''Identify function level coverage map items.'''
    pcMap = compiled['pcMap']
    fn_map = {}
    for op in _oplist(pcMap, "JUMPDEST"):
        s = _get_source(op)
        if s[:8] in ("contract", "library ", "interfac"):
            continue
        if s[:8] == "function":
            fn = s[9:s.index('(')]
        elif " public " in s:
            fn = s[s.index(" public ")+8:].split(' =')[0].strip()
        else:
            continue
        if fn not in fn_map:
            fn_map[fn] = _base(op)
            fn_map[fn]['method'] = fn
        fn_map[fn]['pc'].add(op['pc'])

    fn_map = _sort(fn_map.values())
    if not fn_map:
        return []
    for op in _oplist(pcMap):
        try:
            f = _next(fn_map, op)
        except StopIteration:
            continue
        if op['stop'] > f['stop']:
            continue
        f['pc'].add(op['pc'])
    return fn_map


def _isolate_lines(compiled):
    '''Identify line based coverage map items.

    For lines where a JUMPI is not present, coverage items will merge
    to include as much of the line as possible in a single item. Where a
    JUMPI is involved, no merge will happen and overlapping non-jump items
    are discarded.'''
    pcMap = compiled['pcMap']
    line_map = {}

    # find all the JUMPI opcodes
    for i in [pcMap.index(i) for i in _oplist(pcMap, "JUMPI")]:
        op = pcMap[i]
        if op['contract'] not in line_map:
            line_map[op['contract']] = []
        # if followed by INVALID or the source contains public, ignore it
        if pcMap[i+1]['op'] == "INVALID" or " public " in _get_source(op):
            continue
        try:
            # JUMPI is to the closest previous opcode that has
            # a different source offset and is not a JUMPDEST
            req = next(
                x for x in pcMap[i-2::-1] if x['contract'] and
                x['op'] != "JUMPDEST" and
                x['start'] + x['stop'] != op['start'] + op['stop']
            )
        except StopIteration:
            continue
        line_map[op['contract']].append(_base(req))
        line_map[op['contract']][-1].update({'jump': op['pc']})

    # analyze all the opcodes
    for op in _oplist(pcMap):
        # ignore code that spans multiple lines
        if ';' in _get_source(op):
            continue
        if op['contract'] not in line_map:
            line_map[op['contract']] = []
        # find existing related coverage map item, make a new one if none exists
        try:
            ln = _next(line_map[op['contract']], op)
        except StopIteration:
            line_map[op['contract']].append(_base(op))
            continue
        if op['stop'] > ln['stop']:
            # if coverage map item is a jump, do not modify the source offsets
            if ln['jump']:
                continue
            ln['stop'] = op['stop']
        ln['pc'].add(op['pc'])

    # sort the coverage map and merge overlaps where possible
    for contract in line_map:
        line_map[contract] = _sort(line_map[contract])
        ln_map = line_map[contract]
        i = 0
        while True:
            if len(ln_map) <= i + 1:
                break
            if ln_map[i]['jump']:
                i += 1
                continue
            # JUMPI overlaps cannot merge
            if ln_map[i+1]['jump']:
                if ln_map[i]['stop'] > ln_map[i+1]['start']:
                    del ln_map[i]
                else:
                    i += 1
                continue
            if ln_map[i]['stop'] >= ln_map[i+1]['start']:
                ln_map[i]['pc'] |= ln_map[i+1]['pc']
                ln_map[i]['stop'] = max(ln_map[i]['stop'], ln_map[i+1]['stop'])
                del ln_map[i+1]
                continue
            i += 1
    return [x for v in line_map.values() for x in v]


def _get_source(op):
    if op['contract'] not in _sources:
        _sources[op['contract']] = open(op['contract']).read()
    return _sources[op['contract']][op['start']:op['stop']]


def _next(coverage_map, op):
    '''Given a coverage map and an item from pcMap, returns the related
    coverage map item (based on source offset overlap).'''
    return next(
        i for i in coverage_map if i['contract'] == op['contract'] and
        i['start'] <= op['start'] < i['stop']
    )


def _sort(list_):
    return sorted(list_, key=lambda k: (k['contract'], k['start'], k['stop']))


def _oplist(pcMap, op=None):
    return [i for i in pcMap if i['contract'] and (not op or op == i['op'])]


def _base(op):
    return {
        'contract': op['contract'],
        'start': op['start'],
        'stop': op['stop'],
        'pc': set([op['pc']]),
        'jump': False
    }
