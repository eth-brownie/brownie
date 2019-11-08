# CHANGELOG

All notable changes to this project are documented in this file.

This changelog format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased](https://github.com/iamdefinitelyahuman/brownie)
### Fixed
- use `isinstance` instead of `type` for conversions, fixes hexstring comparison bug
- pretty printing for more objects in the console
- properly display `SyntaxError` in console when there is no source highlight

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
