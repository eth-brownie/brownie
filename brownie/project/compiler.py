#!/usr/bin/python3

from copy import deepcopy
from collections import deque
from hashlib import sha1
import solcast
from solcast.utils import is_inside_offset
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


def compile_and_format(contracts, silent=True):
    '''Compiles contracts and returns build data.

    Args:
        contracts: a dictionary in the form of {path: 'source code'}
    '''
    if not contracts:
        return {}

    input_json = generate_input_json(contracts, CONFIG['solc']['minify_source'])
    output_json = compile_contracts(input_json, silent)
    build_json = generate_build_json(input_json, output_json, silent)
    return build_json


def generate_input_json(contracts, minify=False):
    '''Formats contracts to the standard solc input json.

    Args:
        contracts: a dictionary in the form of {path: 'source code'}
        minify: should source code be minified?

    Returns: dict
    '''
    input_json = STANDARD_JSON.copy()
    input_json['sources'] = dict((
        k,
        {'content': sources.minify(v)[0] if minify else v}
    ) for k, v in contracts.items())
    return input_json


def compile_contracts(input_json, silent=True):
    '''Compiles contracts from a standard input json.

    Args:
        input_json: solc input json

    Returns: standard compiler output json'''
    optimizer = input_json['settings']['optimizer']
    if not silent:
        print("Compiling contracts...")
        print("Optimizer: {}".format(
            "Enabled  Runs: "+str(optimizer['runs']) if
            optimizer['enabled'] else "Disabled"
        ))
    try:
        return solcx.compile_standard(
            input_json,
            optimize=optimizer['enabled'],
            optimize_runs=optimizer['runs'],
            allow_paths="."
        )
    except solcx.exceptions.SolcError as e:
        raise CompilerError(e)


def generate_build_json(input_json, output_json, silent=True):
    '''Formats standard compiler output to the brownie build json.

    Args:
        input_json: solc input json used to compile
        output_json: output json returned by compiler

    Returns: build json dict'''
    build_json = {}
    path_list = list(input_json['sources'])
    source_nodes = solcast.from_standard_output(deepcopy(output_json))

    for path, contract_name in [(k, v) for k in path_list for v in output_json['contracts'][k]]:

        if not silent:
            print(" - {}...".format(contract_name))
        evm = output_json['contracts'][path][contract_name]['evm']
        node = next(i[contract_name] for i in source_nodes if i.name == path)
        bytecode = format_link_references(evm)

        pc_list = generate_pc_list(
            evm['deployedBytecode']['sourceMap'],
            evm['deployedBytecode']['opcodes'],
            node
        )

        paths = sorted(set([node.parent.path]+[i.parent.path for i in node.dependencies]))

        build_json[contract_name] = {
            'abi': output_json['contracts'][path][contract_name]['abi'],
            'allSourcePaths': paths,
            'ast': output_json['sources'][path]['ast'],
            'bytecode': bytecode,
            'bytecodeSha1': sha1(bytecode[:-68].encode()).hexdigest(),
            'compiler': dict(CONFIG['solc']),
            'contractName': contract_name,
            'coverageMap': {},  # TODO reimplement
            'coverageMapTotals': {},
            'deployedBytecode': evm['deployedBytecode']['object'],
            'deployedSourceMap': evm['deployedBytecode']['sourceMap'],
            'dependencies': [i.name for i in node.dependencies],
            # 'networks': {},
            'fn_offsets': [[node.name+'.'+i.name, i.offset] for i in node.functions],
            'offset': node.offset,
            'opcodes': evm['deployedBytecode']['opcodes'],
            'pcMap': pc_list_to_map(pc_list),
            'sha1': sources.get_hash(contract_name),
            'source': input_json['sources'][path]['content'],
            'sourceMap': evm['bytecode']['sourceMap'],
            'sourcePath': path,
            'type': node.type
        }
    return build_json


def format_link_references(evm):
    '''Standardizes formatting for unlinked libraries within bytecode.'''
    bytecode = evm['bytecode']['object']
    references = [(k, x) for v in evm['bytecode']['linkReferences'].values() for k, x in v.items()]
    for n, loc in [(i[0], x['start']*2) for i in references for x in i[1]]:
        bytecode = "{}__{:_<36}__{}".format(
            bytecode[:loc],
            n[:36],
            bytecode[loc+40:]
        )
    return bytecode


def generate_pc_list(source_map, opcodes, contract_node):
    '''
    Generates an expanded sourceMap useful for debugging. Values that would be
    False are not included.

    Arguments:
        source_nodes: List of SourceUnit objects
        build_json:

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
    if not opcodes:
        return []

    source_map = deque(expand_source_map(source_map))
    opcodes = deque(opcodes.split(" "))
    id_map = dict((i.contract_id, i) for i in [contract_node]+contract_node.dependencies)
    pc_list = []
    pc = 0

    while source_map:
        source = source_map.popleft()
        pc_list.append({'op': opcodes.popleft(), 'pc': pc})
        pc += 1
        if source[3] != "-":
            pc_list[-1]['jump'] = source[3]
        if opcodes[0][:2] == "0x":
            pc_list[-1]['value'] = opcodes.popleft()
            pc += int(pc_list[-1]['op'][4:])
        if source[2] == -1:
            continue
        node = id_map[source[2]]
        pc_list[-1]['path'] = node.parent.path
        if source[0] == -1:
            continue
        offset = [source[0], source[0]+source[1]]
        pc_list[-1]['offset'] = offset
        try:
            pc_list[-1]['fn'] = node.child_by_offset(offset).full_name
        except KeyError:
            pass

    return pc_list


def pc_list_to_map(pc_list):
    '''Convert a pc list to a pc map'''
    return dict((i.pop('pc'), i) for i in pc_list)


def expand_source_map(source_map):
    '''Expands the compressed sourceMap supplied by solc into a list of lists.'''
    source_map = [_expand_row(i) if i else None for i in source_map.split(';')]
    for i in range(1, len(source_map)):
        if not source_map[i]:
            source_map[i] = source_map[i-1]
            continue
        for x in range(4):
            if source_map[i][x] is None:
                source_map[i][x] = source_map[i-1][x]
    return source_map


def _expand_row(row):
    row = row.split(':')
    return [int(i) if i else None for i in row[:3]] + row[3:] + [None]*(4-len(row))


def get_statement_map(contract_node, pc_list):
    if not pc_list:
        return []
    pc_list = [i for i in pc_list if 'offset' in i and i['path'] == contract_node.parent.path]
    statement_map = []
    for node in contract_node.children(include_parents=False, node_class="Statement"):
        if node.root(2).name == "<constructor>":
            continue
        try:
            pc = next(i['pc'] for i in pc_list if is_inside_offset(i['offset'], node.offset))
        except StopIteration:
            continue
        statement_map.append([pc, node.offset])
    return statement_map


def get_branch_map(contract_node, pc_list):
    if not pc_list:
        return []
    pc_list = [i for i in pc_list if 'offset' in i and i['path'] == contract_node.parent.path]
    branch_map = []

    # require branches
    for node in contract_node.children(node_type="FunctionCall", name="require"):
        if not _get_binary_branches(node, pc_list, branch_map):
            pc = _get_jump(pc_list, node.offset)
            if pc:
                branch_map.append([pc, node.arguments[0].offset])

    # if statement branches
    for node in contract_node.children(node_type="IfStatement"):
        if not _get_binary_branches(node.condition, pc_list, branch_map):
            pc = _get_jump(pc_list, node.offset)
            if pc:
                branch_map.append([pc, node.condition.offset])

    # ternery operator branches
    for node in contract_node.children(node_type="Conditional"):
        if not _get_binary_branches(node.condition, pc_list, branch_map):
            pc = _get_jump(pc_list, node.condition.offset, True)
            if pc:
                branch_map.append([pc, node.condition.offset])

    return branch_map


def _get_binary_branches(base_node, pc_list, branch_map):

    # get all child binaries, including self and binaries that are parents
    all_binaries = base_node.children(
        include_parents=True,
        include_self=True,
        node_type="BinaryOperation",
        type="bool"
    )

    # if base node contains no binaries, return False to allow use of different node offset
    if not all_binaries:
        return False

    for node in all_binaries:
        # if node has no child binaries, include it
        if not node.children(include_self=False, node_type="BinaryOperation", type="bool"):
            pc = _get_jump(pc_list, node.offset)
            if pc:
                branch_map.append([pc, node.offset])
            continue
        # otherwise, check immediate children
        for node in (node.left, node.right):
            # if node has a child binary or is a binary, ignore it
            if node.children(include_self=True, node_type="BinaryOperation", type="bool"):
                continue
            # otherwise, include it
            pc = _get_jump(pc_list, node.offset)
            if pc:
                branch_map.append([pc, node.offset])
    return True


def _get_jump(pc_list, offset, reverse=False):
    iterable = reversed(pc_list) if reverse else pc_list
    pc = next((i['pc'] for i in iterable if i['offset'] == offset), None)
    if pc is None:
        iterable = reversed(pc_list) if reverse else pc_list
        pc = next((i['pc'] for i in iterable if is_inside_offset(i['offset'], offset)), None)
    if pc is None:
        return None
    return next(i['pc'] for i in pc_list if i['pc'] > pc and i['op'] == "JUMPI")
