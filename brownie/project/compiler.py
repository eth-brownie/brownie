#!/usr/bin/python3

from copy import deepcopy
from collections import deque
from hashlib import sha1
import solcast
from solcast.utils import is_inside_offset
import solcx

from . import sources
from brownie.exceptions import CompilerError

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
            "enabled": True,
            "runs": 200
        }
    }
}


def set_solc_version(version):
    '''Sets the solc version. If not available it will be installed.'''
    try:
        solcx.set_solc_version(version)
    except solcx.exceptions.SolcNotInstalled:
        solcx.install_solc(version)
        solcx.set_solc_version(version)
    return solcx.get_solc_version_string().strip('\n')


def compile_and_format(contracts, optimize=True, runs=200, minify=False, silent=True):
    '''Compiles contracts and returns build data.

    Args:
        contracts: a dictionary in the form of {path: 'source code'}
        optimize: enable solc optimizer
        runs: optimizer runs
        minify: minify source files
        silent: verbose reporting

    Returns: build data dict'''
    if not contracts:
        return {}

    compiler_data = {
        'minify_source': minify,
        'version': solcx.get_solc_version_string().strip('\n')
    }

    input_json = generate_input_json(contracts, optimize, runs, minify)
    output_json = compile_from_input_json(input_json, silent)
    build_json = generate_build_json(input_json, output_json, compiler_data, silent)
    return build_json


def generate_input_json(contracts, optimize=True, runs=200, minify=False):
    '''Formats contracts to the standard solc input json.

    Args:
        contracts: a dictionary in the form of {path: 'source code'}
        optimize: enable solc optimizer
        runs: optimizer runs
        minify: should source code be minified?

    Returns: dict
    '''
    input_json = deepcopy(STANDARD_JSON)
    input_json['settings']['optimizer']['enabled'] = optimize
    input_json['settings']['optimizer']['runs'] = runs if optimize else False
    input_json['sources'] = dict((
        k,
        {'content': sources.minify(v)[0] if minify else v}
    ) for k, v in contracts.items())
    return input_json


def compile_from_input_json(input_json, silent=True):
    '''Compiles contracts from a standard input json.

    Args:
        input_json: solc input json
        silent: verbose reporting

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


def generate_build_json(input_json, output_json, compiler_data={}, silent=True):
    '''Formats standard compiler output to the brownie build json.

    Args:
        input_json: solc input json used to compile
        output_json: output json returned by compiler
        compiler_data: additonal data to include under 'compiler' in build json
        silent: verbose reporting

    Returns: build json dict'''
    if not silent:
        print("Generating build data...")

    compiler_data.update({
        "optimize": input_json['settings']['optimizer']['enabled'],
        "runs": input_json['settings']['optimizer']['runs']
    })
    minify = 'minify_source' in compiler_data and compiler_data['minify_source']
    build_json = {}
    path_list = list(input_json['sources'])

    source_nodes = solcast.from_standard_output(deepcopy(output_json))
    statement_nodes = get_statement_nodes(source_nodes)
    branch_nodes = get_branch_nodes(source_nodes)

    for path, contract_name in [(k, v) for k in path_list for v in output_json['contracts'][k]]:

        if not silent:
            print(" - {}...".format(contract_name))

        evm = output_json['contracts'][path][contract_name]['evm']
        node = next(i[contract_name] for i in source_nodes if i.name == path)
        bytecode = format_link_references(evm)
        paths = sorted(set([node.parent().path]+[i.parent().path for i in node.dependencies]))

        pc_list, statement_map, branch_map = generate_coverage_data(
            evm['deployedBytecode']['sourceMap'],
            evm['deployedBytecode']['opcodes'],
            node,
            statement_nodes,
            branch_nodes
        )

        build_json[contract_name] = {
            'abi': output_json['contracts'][path][contract_name]['abi'],
            'allSourcePaths': paths,
            'ast': output_json['sources'][path]['ast'],
            'bytecode': bytecode,
            'bytecodeSha1': get_bytecode_hash(bytecode),
            'compiler': compiler_data,
            'contractName': contract_name,
            'coverageMap': {'statements': statement_map, 'branches': branch_map},
            'deployedBytecode': evm['deployedBytecode']['object'],
            'deployedSourceMap': evm['deployedBytecode']['sourceMap'],
            'dependencies': [i.name for i in node.dependencies],
            # 'networks': {},
            'fn_offsets': [[node.name+'.'+i.name, i.offset] for i in node.functions],
            'offset': node.offset,
            'opcodes': evm['deployedBytecode']['opcodes'],
            'pcMap': pc_list_to_map(pc_list),
            'sha1': sources.get_hash(contract_name, minify),
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


def get_bytecode_hash(bytecode):
    '''Returns a sha1 hash of the given bytecode without metadata.'''
    return sha1(bytecode[:-68].encode()).hexdigest()


def generate_coverage_data(source_map, opcodes, contract_node, statement_nodes, branch_nodes):
    '''
    Generates data used by Brownie for debugging and coverage evaluation.

    Arguments:
        source_map: compressed SourceMap from solc compiler
        opcodes: deployed bytecode opcode string from solc compiler
        contract_node: ContractDefinition AST node object generated by solc-ast
        statement_nodes: statement node objects from get_statement_nodes
        branch_nodes: branch node objects from get_branch_nodes

    Returns:
        pc_list: expanded source mapping as a list
        statement_map: statement coverage map
        branch_map: branch coverage map

    pc_list is formatted as follows. Keys where the value is False are excluded.

    [{
        'path': relative path of the contract source code
        'jump': jump instruction as supplied in the sourceMap (-,i,o)
        'op': opcode string
        'pc': program counter as given by debug_traceTransaction
        'offset': source code start and stop offsets
        'value': value of the instruction
        'branch': branch coverage index
        'statement': statement coverage index
    }, ... ]

    statement_map and branch_map are formatted as follows:

    {'path/to/contract': { coverage_index: (start, stop), ..}, .. }
    '''
    if not opcodes:
        return [], {}, {}

    source_map = deque(expand_source_map(source_map))
    opcodes = deque(opcodes.split(" "))
    id_map = dict((i.contract_id, i) for i in [contract_node]+contract_node.dependencies)
    paths = set(v.parent().path for v in id_map.values())

    statement_nodes = dict((i, statement_nodes[i].copy()) for i in paths)
    statement_map = dict((i, {}) for i in paths)

    # possible branch offsets
    branch_original = dict((i, branch_nodes[i].copy()) for i in paths)
    branch_nodes = dict((i, set(i.offset for i in branch_nodes[i])) for i in paths)
    # currently active branches, awaiting a jumpi
    branch_active = dict((i, {}) for i in paths)
    # branches that have been set
    branch_set = dict((i, {}) for i in paths)

    count, pc = 0, 0
    pc_list = []

    while source_map:

        # format of source is [start, stop, contract_id, jump code]
        source = source_map.popleft()
        pc_list.append({'op': opcodes.popleft(), 'pc': pc})
        pc += 1

        if source[3] != "-":
            pc_list[-1]['jump'] = source[3]

        if opcodes[0][:2] == "0x":
            pc_list[-1]['value'] = opcodes.popleft()
            pc += int(pc_list[-1]['op'][4:])

        # set contract path (-1 means none)
        if source[2] == -1:
            continue
        node = id_map[source[2]]
        path = node.parent().path
        pc_list[-1]['path'] = path

        # set source offset (-1 means none)
        if source[0] == -1:
            continue
        offset = (source[0], source[0]+source[1])
        pc_list[-1]['offset'] = offset

        # if op is jumpi, set active branch markers
        if branch_active[path] and pc_list[-1]['op'] == "JUMPI":
            for offset in branch_active[path]:
                # ( program counter index, JUMPI index)
                branch_set[path][offset] = (branch_active[path][offset], len(pc_list)-1)
            branch_active[path].clear()

        # if op relates to previously set branch marker, clear it
        elif offset in branch_nodes[path]:
            if offset in branch_set[path]:
                del branch_set[path][offset]
            branch_active[path][offset] = len(pc_list)-1

        try:
            # set fn name and statement coverage marker
            if 'offset' in pc_list[-2] and offset == pc_list[-2]['offset']:
                pc_list[-1]['fn'] = pc_list[-2]['fn']
            else:
                pc_list[-1]['fn'] = node.child_by_offset(offset).full_name
                statement = next(
                    i for i in statement_nodes[path] if
                    is_inside_offset(offset, i)
                )
                statement_nodes[path].discard(statement)
                statement_map[path].setdefault(pc_list[-1]['fn'], {})[count] = statement
                pc_list[-1]['statement'] = count
                count += 1
        except (KeyError, IndexError, StopIteration):
            continue

    # set branch index markers and build final branch map
    source_nodes = dict((i.parent().path, i.parent()) for i in id_map.values())
    branch_map = dict((i, {}) for i in paths)
    for path, offset, idx in [(k, x, y) for k, v in branch_set.items() for x, y in v.items()]:
        # for branch to be hit, need an op relating to the source and the next JUMPI
        # this is because of how the compiler optimizes nested BinaryOperations
        pc_list[idx[0]]['branch'] = count
        pc_list[idx[1]]['branch'] = count
        if 'fn' in pc_list[idx[0]]:
            fn = pc_list[idx[0]]['fn']
        else:
            fn = source_nodes[path].child_by_offset(offset, 2).full_name
        node = next(i for i in branch_original[path] if i.offset == offset)
        branch_map[path].setdefault(fn, {})[count] = offset+(node.jump,)
        count += 1

    return pc_list, statement_map, branch_map


def pc_list_to_map(pc_list):
    '''Convert a program counter list to a program counter map.'''
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


def get_statement_nodes(source_nodes):
    '''Given a list of source nodes, returns a dict of lists of statement nodes.'''
    statements = {}
    for node in source_nodes:
        statements[node.path] = set(i.offset for i in node.children(
            include_parents=False,
            filters={'node_class': "Statement"},
            exclude={'name': "<constructor>"}
        ))
    return statements


def get_branch_nodes(source_nodes):
    '''Given a list of source nodes, returns a dict of lists of nodes corresponding
    to possible branches in the code.'''
    branches = {}
    for node in source_nodes:
        branches[node.path] = set()
        for child_node in node.children(filters=(
            {'node_type': "FunctionCall", 'name': "require"},
            {'node_type': "IfStatement"},
            {'node_type': "Conditional"}
        )):
            branches[node.path] |= _get_recursive_branches(child_node)
    return branches


def _get_recursive_branches(base_node):
    # if node is IfStatement or Conditional, look only at the condition
    jump = True if base_node.node_type == "FunctionCall" else False
    node = base_node.condition if hasattr(base_node, 'condition') else base_node
    depth = base_node.depth

    filters = {'node_type': "BinaryOperation", 'type': "bool"}
    all_binaries = node.children(include_parents=True, include_self=True, filters=filters)

    # if no BinaryOperation nodes are found, this node is the branch
    if not all_binaries:
        # if node is FunctionaCall, look at the first argument
        if not hasattr(base_node, 'condition'):
            node.arguments[0].jump = jump
            return set([node.arguments[0]])
        node.jump = jump
        return set([node])

    # look at BinaryOperation nodes to find all possible branches
    binary_branches = set()
    for node in all_binaries:
        # if node has no BinaryOperation children, include it
        if not node.children(include_self=False, filters=filters):
            if _is_rightmost_operation(node, depth):
                node.jump = jump
            else:
                node.jump = _check_left_operator(node, depth)
            binary_branches.add(node)
            continue
        # otherwise, include the immediate children if they are not BinaryOperations
        for node in (node.left, node.right):
            if node.children(include_self=True, filters=filters):
                continue
            if _is_rightmost_operation(node, depth):
                node.jump = jump
            else:
                node.jump = _check_left_operator(node, depth)
            binary_branches.add(node)

    return binary_branches


def _is_rightmost_operation(node, depth):
    '''Check if the node is the final operation within the expression.'''
    parents = node.parents(depth, {'node_type': "BinaryOperation", 'type': "bool"})
    return not next((i for i in parents if i.left == node or node.is_child_of(i.left)), False)


def _check_left_operator(node, depth):
    '''Find the nearest parent boolean where this node sits on the left side of
    the comparison, and return True if that node's operator is ||'''
    parents = node.parents(depth, {'node_type': "BinaryOperation", 'type': "bool"})
    return next(i for i in parents if i.left == node or node.is_child_of(i.left)).operator == "||"
