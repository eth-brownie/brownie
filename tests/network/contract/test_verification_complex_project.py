"""
Standard input JSON verification test
There are tested following features:
- the same file names for multiple contracts
- relative path in `remappings` not included in `dependencies`
- deploy contract depending on libraries with known address
- fetching different `import` syntax combinations


File structure is folowing, where:
`libs` directory of external libraries
`dir/dir/project-name/project-sources` directory where custom contracts are saved

├── dir
│   └── dir
│       └── project-name
│           ├── brownie-config.yaml
│           └── project-sources
│               ├── c.sol
│               ├── dir
│               │   ├── c.sol
│               │   ├── dir
│               │   │   └── c.sol
│               │   └── d.sol
│               ├── d.sol
│               ├── external_libs.sol
│               ├── import.sol
│               └── lib_tests
│                   ├── import_external_lib.sol
│                   ├── import_project_lib.sol
│                   └── project_lib.sol
└── libs
    ├── lib1
    │   └── c.sol
    └── lib2
        ├── c1.sol
        ├── c.sol
        └── lib
            └── c.sol

"""
import os
import re
from pathlib import Path

import pytest
import solcx
import yaml

from brownie.exceptions import UndeployedLibrary
from brownie.project import load

STRUCTURE = {
    "dir/dir/project-name/brownie-config.yaml": """
project_structure:
  contracts: project-sources

compiler:
  solc:
    remappings:
      - "@lib2/my-organization/new-version/sth-else=../../../libs/lib2"
      # passed trailed slashes /
      - "@fancy-lib-name//////=../../../libs/lib1//"

libraries:
  Lib0: '0xA0A0A0A0A0A0A0A0A0A0A0A0A0A0A0A0A0A0A0A0'
  Lib1: '0xB1B1B1B1B1B1B1B1B1B1B1B1B1B1B1B1B1B1B1B1'
  Lib2: '0xC2C2C2C2C2C2C2C2C2C2C2C2C2C2C2C2C2C2C2C2'
  Lib3: '0xD3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3'

""",
    "dir/dir/project-name/project-sources/c.sol": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract C0 {}

""",
    "dir/dir/project-name/project-sources/d.sol": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import './c.sol';
import './dir/d.sol';

contract D2 is C0, D1 {}

""",
    "dir/dir/project-name/project-sources/dir/c.sol": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract C_1 { function c_1() public view {} }

""",
    "dir/dir/project-name/project-sources/dir/d.sol": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import './c.sol';

contract D1 is C_1 {}

""",
    "dir/dir/project-name/project-sources/dir/dir/c.sol": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract C { function c() public pure {} }
contract C1 { function c1() public pure {} }
contract C2 { function c2() public pure {} }
contract C3 { function c3() public pure {} }
contract C4 { function c4() public pure {} }
""",
    "dir/dir/project-name/project-sources/external_libs.sol": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;


// import { MainContract } from './import.sol';

import { Lib2, Lib3 } from
'@lib2/my-organization/new-version/sth-else/lib/c.sol';

import
"@lib2/my-organization/new-version/sth-else/c.sol";

import "@lib2/my-organization/new-version/sth-else/c1.sol";

import '@fancy-lib-name/c.sol';

import './c.sol';


contract ExternalLibs is
DoNothing,
C0
{
    using Lib0 for uint256;
    using Lib1 for uint256;
    using Lib2 for uint256;
    using Lib3 for uint256;

    uint256 public state = 5;

    function useLibs(uint256 arg) public {
        state =
        state.doNothing() +
        arg.lib1().lib2().lib3().doNothing();
    }
}

""",
    "dir/dir/project-name/project-sources/import.sol": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/* messed import syntaxes */

      import        './c.sol'  ;


import

{

    C,
    C1 as C_dir_C1,

    C2
    as
    C_dir_c2,

    C3

    as

    import_c3  ,

    C4
    as

    c4_import
}



from


    './dir/../dir/../dir/dir/../dir/c.sol'

       ;


import   "./dir/c.sol"
as VIPimportSol
;

// invalid import syntax, uncomment to get compilation error
// import      '   ../Lib2
// .sol   ';

contract
  importCon

is
 C,
   C_dir_C1,
   import_c3,

   c4_import
{
  function doSth() public pure {}
}


contract CoNimport is

C0,
VIPimportSol.C_1,
C_dir_c2,
C_dir_C1

{
  function doSth() public pure {}
}


contract MainContract {
    function doSomething(address addr1, address addr2) public pure {
      // import in variables name
      importCon import_con = importCon (addr1) ;
      CoNimport con_import = CoNimport(addr2);
      import_con.doSth();
      con_import.doSth();
    }

}

""",
    "dir/dir/project-name/project-sources/lib_tests/import_external_lib.sol": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import '@fancy-lib-name/c.sol';

contract import_external_lib {
    using Lib1 for uint256;

    function addOne(uint256 arg) public pure returns(uint256) {
        return arg.lib1();
    }
}

""",
    "dir/dir/project-name/project-sources/lib_tests/import_project_lib.sol": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import './project_lib.sol';

contract import_project_lib {
    using project_lib for string;

    function modify(string memory _str) public pure returns(string memory) {
        return _str.returnString();
    }
}

""",
    "dir/dir/project-name/project-sources/lib_tests/project_lib.sol": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

library project_lib {
    function returnString(string calldata str) public pure returns(string memory) {
        return str;
    }
}

""",
    "libs/lib1/c.sol": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

library Lib1 {
    function lib1(uint256 self) public pure returns(uint256) {
        return self + 1;
    }
}

""",
    "libs/lib2/c.sol": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

library Lib0 {
    function doNothing(uint256 arg) external pure returns(uint256) {
        return arg;
    }
}

""",
    "libs/lib2/c1.sol": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import
{
    Lib0
    as
    Util
}
from
'./c.sol';

interface IdoNothing {
    function doNothing(uint256 arg) external returns(uint256);
}


contract
DoNothing
is
IdoNothing

{
    using Util for uint256;

    function doNothing(uint256 arg) public pure returns(uint256) {
        return arg.doNothing();
    }
}

""",
    "libs/lib2/lib/c.sol": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;


library Lib2 {
    function lib2(uint256 self) public pure returns(uint256) {
        return self + 2;
    }
}

library Lib3 {
    function lib3(uint256 self) public pure returns(uint256) {
        return self + 3;
    }
}

""",
}


class set_project_directory(object):
    def __init__(self, path: Path, project):
        self.path = path
        self.origin = Path().absolute()
        self.project = project

    def __enter__(self):
        os.chdir(self.path)

    def __exit__(self, *args, **kwargs):
        os.chdir(self.origin)
        self.project.close()


def _save_structure(root_path: Path, version: str) -> None:
    for path, source in STRUCTURE.items():
        path = Path(root_path).joinpath(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(Path(root_path).joinpath(path), "w") as file:
            old_pragma = re.findall(r"pragma solidity .*;", source)
            file.write(
                source.replace(old_pragma[0], f"pragma solidity {version};")
                if len(old_pragma) == 1
                else source
            )


def _compile_standard_input_json(verification_info: dict) -> dict:
    input_json = verification_info["standard_json_input"]
    compiler_version, _ = verification_info["compiler_version"].split("+")
    input_json["settings"]["outputSelection"] = {
        "*": {"*": ["evm.bytecode", "evm.deployedBytecode", "abi"]}
    }
    return solcx.compile_standard(input_json, solc_version=compiler_version)


@pytest.mark.parametrize("version", ["0.8.9", "0.8.13"])
def test_verification_info_with_libraries(tmp_path_factory, accounts, version):
    root_dir = tmp_path_factory.mktemp("test-simple-libs-linking")
    _save_structure(root_dir, version)
    project_dir = root_dir.joinpath("dir/dir/project-name")
    project = load(project_dir)

    # change cwd to project directory
    with set_project_directory(project_dir, project):
        # this contract depends on lib in project codebase
        import_project_lib_contract = getattr(project, "import_project_lib")
        project_lib = getattr(project, "project_lib")
        lib_address = accounts[0].deploy(project_lib, silent=True).address
        deployed_contract = accounts[0].deploy(import_project_lib_contract, silent=True)
        build = _compile_standard_input_json(import_project_lib_contract.get_verification_info())
        info = build["contracts"]["lib_tests/import_project_lib.sol"]["import_project_lib"]

        assert info["abi"] == deployed_contract.abi
        assert lib_address[2:].lower() in deployed_contract.bytecode
        assert lib_address[2:].lower() in info["evm"]["deployedBytecode"]["object"]
        assert info["evm"]["deployedBytecode"]["object"][:-106] == deployed_contract.bytecode[:-106]

    project.load()
    with set_project_directory(project_dir, project):
        # this contract depends on lib in project codebase
        import_project_lib_contract = getattr(project, "import_project_lib")
        project_lib = getattr(project, "project_lib")
        with pytest.raises(UndeployedLibrary):
            accounts[0].deploy(import_project_lib_contract, silent=True)

        # set library addres in project
        lib_address = "0x" + 20 * "A5"
        project._libraries = {"project_lib": lib_address}
        deployed_contract = accounts[0].deploy(import_project_lib_contract, silent=True)
        build = _compile_standard_input_json(import_project_lib_contract.get_verification_info())
        info = build["contracts"]["lib_tests/import_project_lib.sol"]["import_project_lib"]

        assert info["abi"] == deployed_contract.abi
        assert lib_address[2:].lower() in deployed_contract.bytecode
        assert lib_address[2:].lower() in info["evm"]["deployedBytecode"]["object"]
        assert info["evm"]["deployedBytecode"]["object"][:-106] == deployed_contract.bytecode[:-106]

    project.load()
    with set_project_directory(project_dir, project):
        # this contract depends on lib from external package
        # test remapping
        import_external_lib_contract = getattr(project, "import_external_lib")
        with open(project_dir / "brownie-config.yaml", "r") as file:
            libraries = yaml.load(file)["libraries"]
        lib_address = libraries["Lib1"]
        deployed_contract = accounts[0].deploy(import_external_lib_contract, silent=True)
        build = _compile_standard_input_json(import_external_lib_contract.get_verification_info())
        info = build["contracts"]["lib_tests/import_external_lib.sol"]["import_external_lib"]

        assert info["abi"] == deployed_contract.abi
        assert lib_address[2:].lower() in deployed_contract.bytecode
        assert lib_address[2:].lower() in info["evm"]["deployedBytecode"]["object"]
        assert info["evm"]["deployedBytecode"]["object"][:-106] == deployed_contract.bytecode[:-106]


@pytest.mark.parametrize("version", ["0.8.9", "0.8.13"])
def test_verification_with_multiple_the_same_filenames(tmp_path_factory, accounts, version):
    root_dir = tmp_path_factory.mktemp("test-the-same-file-names")
    _save_structure(root_dir, version)
    project_dir = root_dir.joinpath("dir/dir/project-name")
    project = load(project_dir)

    # test messed imports, like multilines
    with set_project_directory(project_dir, project):
        main_contract = getattr(project, "MainContract")
        deployed_contract = accounts[0].deploy(main_contract, silent=True)
        build = _compile_standard_input_json(main_contract.get_verification_info())
        info = build["contracts"]["import.sol"]["MainContract"]
        assert info["abi"] == deployed_contract.abi
        assert info["evm"]["deployedBytecode"]["object"][:-106] == deployed_contract.bytecode[:-106]

        # test external library linking via remappings
        external_libs_contract = getattr(project, "ExternalLibs")
        with open(project_dir / "brownie-config.yaml", "r") as file:
            libs = yaml.load(file)["libraries"]
        deployed_contract = accounts[0].deploy(external_libs_contract, silent=True)
        build = _compile_standard_input_json(external_libs_contract.get_verification_info())
        info = build["contracts"]["external_libs.sol"]["ExternalLibs"]

        assert info["abi"] == deployed_contract.abi
        assert info["evm"]["deployedBytecode"]["object"][:-106] == deployed_contract.bytecode[:-106]
        for lib_address in libs.values():
            assert lib_address[2:].lower() in deployed_contract.bytecode
            assert lib_address[2:].lower() in info["evm"]["deployedBytecode"]["object"]

        # test deploy contract from inside directory of project structure
        contract = getattr(project, "D1")
        deployed_contract = accounts[0].deploy(contract, silent=True)
        build = _compile_standard_input_json(contract.get_verification_info())
        info = build["contracts"]["dir/d.sol"]["D1"]
        assert info["abi"] == deployed_contract.abi
        assert info["evm"]["deployedBytecode"]["object"][:-106] == deployed_contract.bytecode[:-106]
