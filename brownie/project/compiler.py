#!/usr/bin/python3

from hashlib import sha1
from pathlib import Path
import solcx

from . import sources
from brownie.exceptions import CompilerError
from brownie._config import CONFIG

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


def set_solc_version():
    '''Sets the solc version based on the project config file.'''
    try:
        solcx.set_solc_version(CONFIG['solc']['version'])
    except solcx.exceptions.SolcNotInstalled:
        solcx.install_solc(CONFIG['solc']['version'])
        solcx.set_solc_version(CONFIG['solc']['version'])
    CONFIG['solc']['version'] = solcx.get_solc_version_string().strip('\n')


def compile_contracts(contracts, silent=False):
    '''Compiles contracts and returns a dict of build data.

    Args:
        contracts: a dictionary in the form of {path: 'source code'}
    '''
    if not contracts:
        return {}
    if not silent:
        print("Compiling contracts...")
        print("Optimizer: {}".format(
            "Enabled  Runs: "+str(CONFIG['solc']['runs']) if
            CONFIG['solc']['optimize'] else "Disabled"
        ))
        names = [Path(i).name for i in contracts]
        print("\n".join(" - {}...".format(i) for i in names))
    input_json = STANDARD_JSON.copy()
    input_json['sources'] = dict((k, {'content': v}) for k, v in contracts.items())
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

    result = {}

    compiled = _generate_pcMap(compiled)
    symbols = get_symbol_map(compiled)

    for filename, name in [(k, v) for k in input_json['sources'] for v in compiled['contracts'][k]]:
        evm = compiled['contracts'][filename][name]['evm']
        node = get_contract_node(compiled['sources'][filename]['ast'], name)
        bytecode = format_link_references(evm)
        all_paths = sorted(set(v['path'] for v in evm['pcMap'].values() if v['path']))

        result[name] = {
            'abi': compiled['contracts'][filename][name]['abi'],
            'allSourcePaths': all_paths,
            'ast': compiled['sources'][filename]['ast'],
            'bytecode': bytecode,
            'bytecodeSha1': sha1(bytecode[:-68].encode()).hexdigest(),
            'compiler': dict(CONFIG['solc']),
            'contractName': name,
            'deployedBytecode': evm['deployedBytecode']['object'],
            'deployedSourceMap': evm['deployedBytecode']['sourceMap'],
            'dependencies': get_dependencies(node, symbols, evm['bytecode']['linkReferences']),
            # 'networks': {},
            'fn_offsets': get_fn_offsets(node),
            'offset': get_contract_offset(node),
            'opcodes': evm['deployedBytecode']['opcodes'],
            'pcMap': evm['pcMap'],
            'sha1': sources.get_hash(name),
            'source': input_json['sources'][filename]['content'],
            'sourceMap': evm['bytecode']['sourceMap'],
            'sourcePath': filename,
            'type': node['contractKind']
        }
        result[name]['coverageMap'] = _generate_coverageMap(result[name])
        result[name]['coverageMapTotals'] = _generate_coverageMapTotals(result[name]['coverageMap'])
    return result


def _generate_pcMap(compiled):
    '''
    Generates an expanded sourceMap useful for debugging.
    [{
        'path': relative path of the contract source code
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
            compiled['contracts'][filename][name]['evm']['pcMap'] = {}
            continue
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
        pcMap = {0: {
            'start': last[0],
            'stop': last[0]+last[1],
            'op': opcodes.pop(),
            'path': id_map[last[2]],
        }}
        pcMap[0]['value'] = opcodes.pop()
        for value in source_map.split(';')[1:]:
            if pcMap[pc]['op'][:4] == "PUSH":
                pc += int(pcMap[pc]['op'][4:])
            pc += 1
            if value:
                value = (value+":::").split(':')[:4]
                for i in range(3):
                    value[i] = int(value[i] or last[i])
                value[3] = value[3] or last[3]
                last = value
            contract = id_map[last[2]] if last[2] != -1 else False
            pcMap[pc] = {
                'start': last[0],
                'stop': last[0]+last[1],
                'op': opcodes.pop(),
                'path': contract,
            }
            if last[3] != "-":
                pcMap[pc]['jump'] = last[3]
            if contract:
                fn = sources.get_fn(contract, last[0], last[0]+last[1])
                if fn:
                    pcMap[pc]['fn'] = fn
            if opcodes[-1][:2] == "0x":
                pcMap[pc]['value'] = opcodes.pop()
        compiled['contracts'][filename][name]['evm']['pcMap'] = pcMap
    return compiled


def _generate_coverageMap(build):
    """Adds coverage data to a build json.

    A new key 'coverageMap' is created, structured as follows:

    {
        "/path/to/contract/file.sol": {
            "functionName": [{
                'jump': pc of the JUMPI instruction, if it is a jump
                'start': source code start offest
                'stop': source code stop offset
            }],
        }
    }

    Relevent items in the pcMap also have a 'coverageIndex' added that corresponds
    to an entry in the coverageMap."""
    line_map = _isolate_lines(build)
    if not line_map:
        return {}

    final = dict((i, {}) for i in set(i['path'] for i in line_map))
    for i in line_map:
        fn = sources.get_fn(i['path'], i['start'], i['stop'])
        if not fn:
            continue
        final[i['path']].setdefault(fn, []).append({
            'jump': i['jump'],
            'start': i['start'],
            'stop': i['stop']
        })
        for pc in i['pc']:
            build['pcMap'][pc]['coverageIndex'] = len(final[i['path']][fn]) - 1
    return final


def _generate_coverageMapTotals(coverage_map):
    totals = {'total': 0}
    for path, fn_name in [(k, x) for k, v in coverage_map.items() for x in v]:
        maps = coverage_map[path][fn_name]
        count = len([i for i in maps if not i['jump']]) + len([i for i in maps if i['jump']])*2
        totals[fn_name] = count
        totals['total'] += count
    return totals


def _isolate_lines(compiled):
    '''Identify line based coverage map items.

    For lines where a JUMPI is not present, coverage items will merge
    to include as much of the line as possible in a single item. Where a
    JUMPI is involved, no merge will happen and overlapping non-jump items
    are discarded.'''
    pcMap = compiled['pcMap']
    line_map = {}

    # find all the JUMPI opcodes
    for i in [k for k, v in pcMap.items() if v['path'] and v['op'] == "JUMPI"]:
        op = pcMap[i]
        if op['path'] not in line_map:
            line_map[op['path']] = []
        # if followed by INVALID or the source contains public, ignore it
        if pcMap[i+1]['op'] == "INVALID" or " public " in _get_source(op):
            continue
        try:
            # JUMPI is to the closest previous opcode that has
            # a different source offset and is not a JUMPDEST
            pc = next(
                x for x in range(i - 4, 0, -1) if x in pcMap and
                pcMap[x]['path'] and pcMap[x]['op'] != "JUMPDEST" and
                (pcMap[x]['start'], pcMap[x]['stop']) != (op['start'], op['stop'])
            )
        except StopIteration:
            continue
        line_map[op['path']].append(_base(pc, pcMap[pc]))
        line_map[op['path']][-1].update({'jump': i})

    # analyze all the opcodes
    for pc, op in [(i, pcMap[i]) for i in sorted(pcMap)]:
        # ignore code that spans multiple lines
        if not op['path'] or ';' in _get_source(op):
            continue
        if op['path'] not in line_map:
            line_map[op['path']] = []
        # find existing related coverage map item, make a new one if none exists
        try:
            ln = next(
                i for i in line_map[op['path']] if
                i['path'] == op['path'] and
                i['start'] <= op['start'] < i['stop']
            )
        except StopIteration:
            line_map[op['path']].append(_base(pc, op))
            continue
        if op['stop'] > ln['stop']:
            # if coverage map item is a jump, do not modify the source offsets
            if ln['jump']:
                continue
            ln['stop'] = op['stop']
        ln['pc'].add(pc)

    # sort the coverage map and merge overlaps where possible
    for contract in line_map:
        line_map[contract] = sorted(
            line_map[contract],
            key=lambda k: (k['path'], k['start'], k['stop'])
        )
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
    return sources.get(op['path'])[op['start']:op['stop']]


def _base(pc, op):
    return {
        'path': op['path'],
        'start': op['start'],
        'stop': op['stop'],
        'pc': set([pc]),
        'jump': False
    }


def _src_to_offsets(src):
    src = [int(i) for i in src.split(':')[:2]]
    return src[0], src[0]+src[1]


def get_contract_node(build_ast, contract_name):
    return next(
        i for i in build_ast['nodes'] if
        i['nodeType'] == "ContractDefinition"
        and i['name'] == contract_name
    )


def get_contract_offset(ast_node):
    return _src_to_offsets(ast_node['src'])


def get_fn_offsets(ast_node):
    return [(
        i['name'],
        _src_to_offsets(i['src'])
    ) for i in ast_node['nodes'] if i['nodeType'] == "FunctionDefinition" and i['name']][::-1]


def get_symbol_map(output_json):
    symbols = {}
    for ast in [v['ast'] for v in output_json['sources'].values()]:
        symbols.update((v[0], k) for k, v in ast['exportedSymbols'].items())
    return symbols


def get_dependencies(ast_node, symbol_map, link_references):
    return True
    dependencies = [k for v in link_references.values() for k in v.keys()]
    dependencies += [symbol_map[i] for i in ast_node['contractDependencies']]
    dependencies += [i['libraryName']['name'] for i in ast_node['nodes'] if 'libraryName' in i]
    return sorted(dependencies)


def format_link_references(evm):
    bytecode = evm['bytecode']['object']
    references = [(k, x) for v in evm['bytecode']['linkReferences'].values() for k, x in v.items()]
    for n, loc in [(i[0], x['start']*2) for i in references for x in i[1]]:
        bytecode = "{}__{:_<36}__{}".format(
            bytecode[:loc],
            n[:36],
            bytecode[loc+40:]
        )
    return bytecode
