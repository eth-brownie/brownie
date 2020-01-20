# CHANGELOG

All notable changes to this project are documented in this file.

This changelog format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased](https://github.com/iamdefinitelyahuman/brownie)

### Fixed
- Correctly isolate path and nodeid from test cases inside classes

## [1.5.0](https://github.com/iamdefinitelyahuman/brownie/tree/v1.5.0) - 2020-01-20
### Added
- `interfaces/` folder for interface sources
- Support for `pytest-xdist`
- Tested support for Vyper with ethPM
- Progress bar when downloading a Brownie mix
- `get_abi` method for Solidity and Vyper compilers
- Create `.gitignore` and `.gitattributes` when initializing new project

### Changed
- Move check for new contract sources from `Project.__init__` to `Project.load`
- Set `istanbul` as default EVM ruleset, run tests against `ganache-cli` [v6.8.2](https://github.com/trufflesuite/ganache-cli/releases/tag/v6.8.2)

### Deprecated
- `pytest.reverts` is deprecated in favor of `brownie.reverts`

### Fixed
- Check pragma statements when determining if a contract should be recompiled
- Understand `abstract contract` when regexing contract source

## [1.4.2](https://github.com/iamdefinitelyahuman/brownie/tree/v1.4.2) - 2020-01-10
### Added
- Add Ethereum Classic networks in `brownie-config.yaml`
- Accept `atlantis` and `agharta` as EVM ruleset options in `brownie-config.yaml`

### Changed
- Use Vyper [v0.1.0-beta16](https://github.com/vyperlang/vyper/releases/tag/v0.1.0-beta.16)

### Fixed
- Create `~/.brownie/accounts` when `accounts` commandline interface is called

## [1.4.1](https://github.com/iamdefinitelyahuman/brownie/tree/v1.4.1) - 2020-01-09
### Changed
- Do not install solc until required for compilation
- Adjust compiler config settings to be less Solidity-centric

### Fixed
- Compiler bug when generating Vyper branch paths
- Permission error when launching Brownie with Ganache already running on OSX

## [1.4.0](https://github.com/iamdefinitelyahuman/brownie/tree/v1.4.0) - 2020-01-07
### Added
- support for Vyper smart contracts ([v0.1.0-beta15](https://github.com/vyperlang/vyper/releases/tag/v0.1.0-beta.15))
- `brownie accounts` commandline interface

## [1.3.2](https://github.com/iamdefinitelyahuman/brownie/tree/v1.3.2) - 2020-01-01
### Added
- error message for modulus by zero
- progress bar when installing new version of solc

## [1.3.1](https://github.com/iamdefinitelyahuman/brownie/tree/v1.3.1) - 2019-12-25
### Added
- better error message for division by zero

### Fixed
- Correctly save minified source offsets in build artifacts
- Coverage evaluation: isolate `active_branches` between jumps

## [1.3.0](https://github.com/iamdefinitelyahuman/brownie/tree/v1.3.0) - 2019-12-20
### Added
- support for Solidity [v0.6.0](https://github.com/ethereum/solidity/releases/tag/v0.6.0)
- allow `istanbul` as choice for EVM ruleset (default is still `petersburg`)
- allow `dev:` revert comments for `assert` statements
- better error messages when sending ether to nonpayable function, or trying to access an invalid array index

### Fixed
- GUI properly highlights `JUMPDEST` targets within first 256 bytes
- Close IO objects to avoid warnings on exit

## [1.2.1](https://github.com/iamdefinitelyahuman/brownie/tree/v1.2.1) - 2019-11-28
### Added
- cache available solc compiler versions to avoid repeated calls
- store data files in `~/.brownie/`

### Fixed
- removed Tkinter dependency when not loading the GUI

## [1.2.0](https://github.com/iamdefinitelyahuman/brownie/tree/v1.2.0) - 2019-11-23
### Added
- [ethPM](https://docs.ethpm.com/) integration
- `ProjectContract` objects persist between sessions (when enabled in the config file)

### Changed
- `scripts.run` only works when a project is loaded, supports multiple loaded projects

### Fixed
- use `isinstance` instead of `type` for conversions, fixes hexstring comparison bug
- pretty printing for more objects in the console
- properly display `SyntaxError` in console when there is no source highlight
- improved regex statement for finding individual contracts within source files
- favor `==x.x` dependencies over `>=x.x <x.y`, removed deps-of-deps to reduce conflicts
- delete stale compiler artifacts from `build/contracts/` when contract name has changed within the same source file

## [1.1.0](https://github.com/iamdefinitelyahuman/brownie/tree/v1.1.0) - 2019-11-04
### Added
- support for Python 3.8

### Changed
- project config files use `YAML` formatting

## [1.0.1](https://github.com/iamdefinitelyahuman/brownie/tree/v1.0.1) - 2019-10-13
### Fixed
- regex pattern for finding contracts in source
- string formatting in cli
- calling `rpc.attach` with no port set

## [1.0.0](https://github.com/iamdefinitelyahuman/brownie/tree/v1.0.0) - 2019-09-24
### Added
- Integration with MythX via `brownie analyze` CLI command
- Support for ENS domains
- Finalize public API, many minor edits!
- replace `broadcast_reverting_tx` with `reverting_tx_gas_limit` in config
- Allow environment variables in config network.hosts
- Add PEP484 annotations to codebase
- Linting: `black`, `mypy`, `isort`

Thanks to [@crawfordleeds](https://github.com/crawfordleeds) and [@dmuhs](https://github.com/dmuhs) for their contributions on this release!

# Beta Releases

Beta releases do not adhere to semver.

## [1.0.0b11](https://github.com/iamdefinitelyahuman/brownie/tree/v1.0.0b11) - 2019-08-18
- Require web3.py version 5, updates based on breaking changes
- Add support for ABIEncoderV2
- Add Project class, allow opening multiple projects at the same time
- Determine solc version using pragma, allow multiple versions in one project
- Set EVM version in config file
- Allow config file comments, change structure
- Add PublicKeyAccount and Contract (via ABI), allow tracebacks on unknown contracts
- Expanded Alert functionality
- Windows bugfixes

## [1.0.0b10](https://github.com/iamdefinitelyahuman/brownie/tree/v1.0.0b10) - 2019-07-21
- Use pytest for unit testing
- remove check module, add check.equals comparison logic to ReturnValue
- Modify coverage evaluation to work with pytest
- remove brownie.types package, move classes to related modules
- replace wei function with Wei class, expand functionality
- add EthAddress and HexString helper classes
- improved formatting for tx.traceback and tx.call_trace

## [1.0.0b9](https://github.com/iamdefinitelyahuman/brownie/tree/v1.0.0b9) - 2019-07-08
- Support for overloaded function names
- Bugfixes
- Minor code changes and improvements

## [1.0.0b8](https://github.com/iamdefinitelyahuman/brownie/tree/v1.0.0b8) - 2019-06-30
- Rebuild of coverage evaluation functionality using contract ASTs
- Split coverage eval results between branches and statements, add GUI support
- Add tracebacks for failed transactions, better call trace formatting
- Allow contract minification before compiling
- Enable output console in GUI (very basic for now)
- Rebuild brownie console using code.InteractiveConsole
- Significant code refactoring and reorganization
- Emphasis on standardized structure across modules and increased ease of testing
- More tests, coverage at 88%

## [1.0.0b7](https://github.com/iamdefinitelyahuman/brownie/tree/v1.0.0b7) - 2019-05-24
- Commented dev revert strings
- Custom exception classes
- Standardize contract outputs
- Add Travis and Tox, test coverage at 67%
- Many bugfixes

## [1.0.0b6](https://github.com/iamdefinitelyahuman/brownie/tree/v1.0.0b6) - 2019-05-14
- Changes to ContractConstructor call arguments
- Bugfixes and minor changes

## [1.0.0b5](https://github.com/iamdefinitelyahuman/brownie/tree/v1.0.0b5) - 2019-05-13
- Use relative paths in build json files
- Revert calls-as-transactions when evaluating coverage
- Significant refactor and optimizations to coverage analysis
- changes to coverageMap format, add coverageMapTotals
- Save coverage data to reports/ subfolder
- Improvements to GUI

## [1.0.0b4](https://github.com/iamdefinitelyahuman/brownie/tree/v1.0.0b4) - 2019-05-08
- Add broadcast_reverting_tx flag
- Use py-solc-x 0.4.0
- Detect and attach to an already active RPC client, better verbosity on RPC exceptions
- Introduce Singleton metaclass and refactor code to take advantage
- Add EventDict and EventItem classes for transaction event logs
- cli.color, add _print_as_dict _print_as_list _dir_color attributes
- Add conversion methods in types.convert
- Remove brownie.utils package, move modules to network and project packages
- Bugfixes and minor changes

## [1.0.0b3](https://github.com/iamdefinitelyahuman/brownie/tree/v1.0.0b3) - 2019-04-26
- major code re-organization and refactoring
- allow skipping contracts with _
- modify test coverage file format
- merge test and coverage components of cli
- only run tests / coverage evaluation if related files have changed
- integrate opview as brownie gui
- many bugfixes and minor changes

## [1.0.0b2](https://github.com/iamdefinitelyahuman/brownie/tree/v1.0.0b2) - 2019-04-14
- add compile command to cli
- bugfix in pypi package requirements
- show numbers on skipped and failing tests

## [1.0.0b1](https://github.com/iamdefinitelyahuman/brownie/tree/v1.0.0b1) - 2019-04-11
- major code re-organization, brownie now works as a package and is installable via pip
- remove os.path in favor of pathlib.Path - allow Windows support
- rebuild brownie console, use compile to check for completed statements
- remove Accounts.mnemonic
- transaction.history is now a custom data class
- save and load accounts using standard encrypted keystore files
- add brownie bake to initialize projects from template
- many bugfixes and minor changes

## [0.9.5](https://github.com/iamdefinitelyahuman/brownie/tree/v0.9.5) - 2019-04-02
- check.true and check.false require booleans to pass
- Allow subfolders within tests/
- Only run specific tests within a file
- More efficient transaction stack trace analysis
- Improvements to compiler efficiency and functionality
- account.transfer accepts data
- add ContractTx.encode_abi
- add ContractContainer.get_method
- Bugfixes

## [0.9.4](https://github.com/iamdefinitelyahuman/brownie/tree/v0.9.4) - 2019-02-25
- Improved console formatting for lists and dicts
- Run method returns list of scripts when no argument is given
- Do not keep mnemonics and private keys in readline history
- Use KwargTuple type for call return values
- Bugfixes

## [0.9.3](https://github.com/iamdefinitelyahuman/brownie/tree/v0.9.3) - 2019-02-20
- Raise ValueError when attempting to modify non-existant config settings
- Modify install script
- Minor bugfixes

## [0.9.2](https://github.com/iamdefinitelyahuman/brownie/tree/v0.9.2) - 2019-02-19
- Add --stable and --dev flags to swap between master and develop branches
- Better verbosity for check.reverts exception string
- Config settings are reset when network resets
- Add default_contract_owner setting

## [0.9.1](https://github.com/iamdefinitelyahuman/brownie/tree/v0.9.1) - 2019-02-18
- Add --always-transact flag for test and coverage
- Do not show individual methods when contract coverage is 0%
- Minor bugfixes

## [0.9.0](https://github.com/iamdefinitelyahuman/brownie/tree/v0.9.0) - 2019-02-16
- Initial release
