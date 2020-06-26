# CHANGELOG

All notable changes to this project are documented in this file.

This changelog format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased](https://github.com/eth-brownie/brownie)
### Fixed
- Less restrictive `default_langauge_version` in pre-commit hooks
- Updated network configs to match mainnet's latest gas limits

## [1.9.4](https://github.com/eth-brownie/brownie/tree/v1.9.4) - 2020-06-21
### Fixed
- Http Requests now send a custom User-Agent (Fixes Kovan api requests) ([#643](https://github.com/eth-brownie/brownie/pull/643))
- Ensure nonce increments prior to sending a new transaction ([#645](https://github.com/eth-brownie/brownie/pull/645))

## [1.9.3](https://github.com/eth-brownie/brownie/tree/v1.9.3) - 2020-06-19
### Added
- Accounts can now be unlocked on development networks ([#633](https://github.com/eth-brownie/brownie/pull/633))

### Fixed
- Parity error messages ([#631](https://github.com/eth-brownie/brownie/pull/631))
- Geth error messages on reverted `eth_call` ([#639](https://github.com/eth-brownie/brownie/pull/639))
- Etherscan source code returned as compiler JSON input ([#637](https://github.com/eth-brownie/brownie/pull/637))
- Enter correct frame on exception with `brownie run -I` ([#638](https://github.com/eth-brownie/brownie/pull/638))
- Always exit with non-zero status on an unhandled exception ([#640](https://github.com/eth-brownie/brownie/pull/640))

## [1.9.2](https://github.com/eth-brownie/brownie/tree/v1.9.2) - 2020-06-08
### Added
- Filter report outputs by source path or contract name ([#626](https://github.com/eth-brownie/brownie/pull/626))

### Fixed
- Delete `required_confs` from transaction parameters prior to making a call ([#620](https://github.com/eth-brownie/brownie/pull/620))
- Handle coverage data and gas profile as `pytest` reports, fixes Windows formatting issues ([#620](https://github.com/eth-brownie/brownie/pull/622))
- Filter fixtures from namespace when using interactive test debugger ([#627](https://github.com/eth-brownie/brownie/pull/627))

## [1.9.1](https://github.com/eth-brownie/brownie/tree/v1.9.1) - 2020-06-07
### Fixed
- Return actual call when running calls as transactions ([#614](https://github.com/eth-brownie/brownie/pull/614))
- Non-zero exit status when using `brownie test` ([#616](https://github.com/eth-brownie/brownie/pull/616))

## [1.9.0](https://github.com/eth-brownie/brownie/tree/v1.9.0) - 2020-06-05
### Added
- Project folder structure is now configurable ([#581](https://github.com/eth-brownie/brownie/pull/581))
- Deployment artifacts can now be saved via project setting `dev_deployment_artifacts: true` ([#590](https://github.com/eth-brownie/brownie/pull/590))
- All deployment artifacts are tracked in `deployments/map.json` ([#590](https://github.com/eth-brownie/brownie/pull/590))
- `required_confs = n / {'required_confs: n}` argument for transactions. Will wait for n confirmations before processing the tx receipt. `n = 0` will immediately return a pending receipt. ([#587](https://github.com/eth-brownie/brownie/pull/587))
- `tx.confirmations` shows number of confirmations, `tx.wait(n)` waits until `tx` has `n` or more confirmations. ([#587](https://github.com/eth-brownie/brownie/pull/587))
- `load_source` hook point ([#584](https://github.com/eth-brownie/brownie/pull/584))
- Support for BIP39 mnemonics ([#585](https://github.com/eth-brownie/brownie/pull/585))
- Expose `block_identifier` for contract calls ([#596](https://github.com/eth-brownie/brownie/pull/596))
- `length` kwarg for `strategy('address')` ([#607](https://github.com/eth-brownie/brownie/pull/607))

### Changed
- `tx.call_trace()` now displays internal and total gas usage ([#564](https://github.com/eth-brownie/brownie/pull/564))
- Default nonce for transactions now takes pending transactions into account. ([#597](https://github.com/eth-brownie/brownie/pull/597))
- Raise more expressive exception on stale fork ([#598](https://github.com/eth-brownie/brownie/pull/598))
- Automatically add middleware when connecting to POA networks ([#602](https://github.com/eth-brownie/brownie/pull/602))
- Hypothesis output includes code highlights ([#605](https://github.com/eth-brownie/brownie/pull/605))

### Fixed
- Geth Traces depth reduced ([#562](https://github.com/eth-brownie/brownie/pull/562))
- Ganache gasCost in traces (ganache bug) ([#562](https://github.com/eth-brownie/brownie/pull/562))
- Decoding error when contracts use the same event signature with different argument indexing ([#575](https://github.com/eth-brownie/brownie/pull/575))
- Repeated alerts will now run indefinitely, instead of twice ([#608](https://github.com/eth-brownie/brownie/pull/608))
- Catch `ZombieProcess` and `NoSuchProcess` when attaching to ganache in OSX ([#574](https://github.com/eth-brownie/brownie/pull/574))
- Snapshotting during failed `@given` tests ([#591](https://github.com/eth-brownie/brownie/pull/591))
- `Rpc.undo` correctly rewinds to immediately before a transaction ([#604](https://github.com/eth-brownie/brownie/pull/604))

A big thank you to [@matnad](https://github.com/matnad) for many contributions during this release!

## [1.8.9](https://github.com/eth-brownie/brownie/tree/v1.8.9) - 2020-05-26
### Changed
- Raise `ValueError` instead of `VirtualMachineError` when the returned RPC error does not contain a data field ([#555](https://github.com/eth-brownie/brownie/pull/555))
- Improve readability of exception when compilation fails while running pytest ([#556](https://github.com/eth-brownie/brownie/pull/556))

### Fixed
- IPC timeout setting ([#554](https://github.com/eth-brownie/brownie/pull/554))
- Pytest import issues ([#556](https://github.com/eth-brownie/brownie/pull/556))

## [1.8.8](https://github.com/eth-brownie/brownie/tree/v1.8.8) - 2020-05-24
### Changed
- Check `web3.eth.accounts` for new unlocked accounts when calling `Accounts.at` ([#551](https://github.com/eth-brownie/brownie/pull/551))

### Fixed
- Apply timeout setting to all web3 provider types ([#549](https://github.com/eth-brownie/brownie/pull/549))
- `KeyError` when handling certain types of RPC errors ([#550](https://github.com/eth-brownie/brownie/pull/550))

## [1.8.7](https://github.com/eth-brownie/brownie/tree/v1.8.7) - 2020-05-23
### Added
- `--interactive` flag when using `brownie run` ([#547](https://github.com/eth-brownie/brownie/pull/547))

### Changed
- Allow connections to `wss://` endpoints ([#542](https://github.com/eth-brownie/brownie/pull/542))
- Improved `--gas` report ([#543](https://github.com/eth-brownie/brownie/pull/543))
- Adjust how gas prices are handled to allow use of web3 gas price API ([#530](https://github.com/eth-brownie/brownie/pull/530))

### Fixed
- Compiler error when on moving contracts ([#545](https://github.com/eth-brownie/brownie/pull/545))
- Allow `timeout` as a field in `brownie networks` CLI ([#533](https://github.com/eth-brownie/brownie/pull/533))
- Issues with interactive debugging in Windows ([#544](https://github.com/eth-brownie/brownie/pull/544))
- Handle selfdestructed contract during deployment ([#546](https://github.com/eth-brownie/brownie/pull/546))

## [1.8.6](https://github.com/eth-brownie/brownie/tree/v1.8.6) - 2020-05-19
### Added
- `contract_strategy` for drawing objects from a `ContractContainer` ([#528](https://github.com/eth-brownie/brownie/pull/528))

### Changed
- Warn on direct import of `hypothesis.given` ([#526](https://github.com/eth-brownie/brownie/pull/526))
- Standardize revert exceptions between calls and transactions ([#527](https://github.com/eth-brownie/brownie/pull/527))

### Fixed
- Ensure correct frame for locals and globals with pytest console debugging ([#523](https://github.com/eth-brownie/brownie/pull/523))
- Add failed tx's to undo buffer prior to raising ([#524](https://github.com/eth-brownie/brownie/pull/524))

## [1.8.5](https://github.com/eth-brownie/brownie/tree/v1.8.5) - 2020-05-14
### Added
- `Account.gas_used` ([#518](https://github.com/eth-brownie/brownie/pull/518))

### Fixed
- Decoding error with arrays of tuples ([#517](https://github.com/eth-brownie/brownie/pull/517))
- Allow pasting multiple commands into the console ([#519](https://github.com/eth-brownie/brownie/pull/519))
- Minor pytest fixes ([#521](https://github.com/eth-brownie/brownie/pull/521))

## [1.8.4](https://github.com/eth-brownie/brownie/tree/v1.8.4) - 2020-05-09
### Added
- `Wei.to` for unit conversion ([#501](https://github.com/eth-brownie/brownie/pull/501))
- Exposed `block_time`, `default_balance` and `time` ganache-cli parameters ([#501](https://github.com/eth-brownie/brownie/pull/501))
- `TransactionReceipt.timestamp` ([#504](https://github.com/eth-brownie/brownie/pull/504))

### Changed
- `brownie-config.yaml` can now specify ganache-cli parameters ([#501](https://github.com/eth-brownie/brownie/pull/501))
- Global variables are now available when using the console for debugging ([#506](https://github.com/eth-brownie/brownie/pull/506))
- Simplified syntax for calling overloaded methods ([#507](https://github.com/eth-brownie/brownie/pull/507))

## [1.8.3](https://github.com/eth-brownie/brownie/tree/v1.8.3) - 2020-05-06
### Changed
- Exposed `nonce` parameter to deploy, transfer and transact methods ([#488](https://github.com/eth-brownie/brownie/pull/488))
- Obtain EVM compiler version and proxy information from Etherscan API ([#492](https://github.com/eth-brownie/brownie/pull/492))
- Better sorting of gas used output ([#491](https://github.com/eth-brownie/brownie/pull/491))

### Fixed
- `Rpc.undo` / `Rpc.redo` with non-instant confirmations ([#483](https://github.com/eth-brownie/brownie/pull/483))
- Minimum solc version when using `Contract.from_explorer` on OSX ([#490](https://github.com/eth-brownie/brownie/pull/490))
- Allow path remappings and imports from packages in interfaces ([#495](https://github.com/eth-brownie/brownie/pull/495))

## [1.8.2](https://github.com/eth-brownie/brownie/tree/v1.8.2) - 2020-05-04
### Fixed
- Allow leading underscores in project root path ([#478](https://github.com/eth-brownie/brownie/pull/478))
- Handle non-string values in pytest print function ([#479](https://github.com/eth-brownie/brownie/pull/479))
- Do not display `.None` for functions name of proxied contract calls ([#481](https://github.com/eth-brownie/brownie/pull/481))

## [1.8.1](https://github.com/eth-brownie/brownie/tree/v1.8.1) - 2020-05-02
### Added
- `--disable-warnings` flag when running tests ([#474](https://github.com/eth-brownie/brownie/pull/474))
- Set custom timeout option for web3 calls ([#469](https://github.com/eth-brownie/brownie/pull/469))

### Changed
- Exposed `silent` parameter to `Account.transfer` ([#472](https://github.com/eth-brownie/brownie/pull/472))

### Fixed
- Import statements within project interfaces ([#475](https://github.com/eth-brownie/brownie/pull/475))

## [1.8.0](https://github.com/eth-brownie/brownie/tree/v1.8.0) - 2020-04-30
### Added
- Interactive debugging mode when running tests ([#456](https://github.com/eth-brownie/brownie/pull/456))
- `Rpc.undo` and `Rpc.redo` ([#457](https://github.com/eth-brownie/brownie/pull/457))
- `InterfaceContainer` and `InterfaceConstructor` ([#463](https://github.com/eth-brownie/brownie/pull/463))
- Allow contract deployment via `Account.transfer` ([#464](https://github.com/eth-brownie/brownie/pull/464))

### Changed
- Do not raise on non-zero block height ([#461](https://github.com/eth-brownie/brownie/pull/461))
- When fetching source code, call `getabi` if `getsourcecode` fails ([#462](https://github.com/eth-brownie/brownie/pull/462))

### Fixed
- Add missing args to pytest `print` method ([#460](https://github.com/eth-brownie/brownie/pull/460))

## [1.7.5](https://github.com/eth-brownie/brownie/tree/v1.7.5) - 2020-04-26
### Fixed
- Importing keystore files from CLI without `.json` suffix ([#448](https://github.com/eth-brownie/brownie/pull/448))
- Properly display reports in GUI ([#449](https://github.com/eth-brownie/brownie/pull/449))


## [1.7.4](https://github.com/eth-brownie/brownie/tree/v1.7.4) - 2020-04-25
### Fixed
- Do not repeat queries for unverified source ([#445](https://github.com/eth-brownie/brownie/pull/445))
- `KeyError` when using `autofetch_sources` ([#445](https://github.com/eth-brownie/brownie/pull/445))
- "No owner" issue with contract call during coverage evaluation ([#446](https://github.com/eth-brownie/brownie/pull/446))

## [1.7.3](https://github.com/eth-brownie/brownie/tree/v1.7.3) - 2020-04-23
### Changed
- Expanded support for use of `--fork` with Ganache ([#437](https://github.com/eth-brownie/brownie/pull/437))

### Fixed
- Remove outdated check for project-inside-project ([#438](https://github.com/eth-brownie/brownie/pull/438))

## [1.7.2](https://github.com/eth-brownie/brownie/tree/v1.7.2) - 2020-04-22
### Fixed
- Properly handle undecodable events ([#433](https://github.com/eth-brownie/brownie/pull/433))

## [1.7.1](https://github.com/eth-brownie/brownie/tree/v1.7.1) - 2020-04-20
### Fixed
- Do not allow `brownie init` on a directory that isn't empty ([#428](https://github.com/eth-brownie/brownie/pull/428))
- Missing dev revert strings on `require` as last statement in a function ([#424](https://github.com/eth-brownie/brownie/pull/424))
- Colorful output when skipping tests without `xdist` ([#422](https://github.com/eth-brownie/brownie/pull/422))

## [1.7.0](https://github.com/eth-brownie/brownie/tree/v1.7.0) - 2020-04-17
### Added
- Install packages from Github or ethPM using `brownie pm` CLI commands ([#390](https://github.com/eth-brownie/brownie/pull/390))
- Manage network settings using `brownie networks` CLI commands ([#408](https://github.com/eth-brownie/brownie/pull/408))
- Fetch contract sources from Etherscan API with `Contract.from_explorer` ([#413](https://github.com/eth-brownie/brownie/pull/413))
- Maintain persistent deployment records in SQLite database ([#413](https://github.com/eth-brownie/brownie/pull/413))
- Use [`prompt_toolkit`](https://github.com/prompt-toolkit/python-prompt-toolkit) in console to enable autocompletion, input suggestions and code highlights ([#416](https://github.com/eth-brownie/brownie/pull/416))
- View NatSpec documentation for contract functions with `ContractCall.info` ([#395](https://github.com/eth-brownie/brownie/pull/395))
- `Accounts.default` to set default account for contract deployments ([#391](https://github.com/eth-brownie/brownie/pull/391))
- Cleaner output when using the `-s` flag with pytest ([#397](https://github.com/eth-brownie/brownie/pull/397))

### Changed
- All configuration file settings are now optional and no config file is added when creating a new project ([#408](https://github.com/eth-brownie/brownie/pull/408))
- Network settings are handled independently of projects ([#408](https://github.com/eth-brownie/brownie/pull/408))
- Paths are referenced via pointers in build artifacts ([#403](https://github.com/eth-brownie/brownie/pull/403))

### Deprecated
- `Contract` init method deprecated in favor of `from_ethpm` or `from_abi` class methods ([#413](https://github.com/eth-brownie/brownie/pull/413))
- `brownie ethpm` CLI tool temporarily deprecated in favor of `brownie pm` until ethPM v3 is official ([#390](https://github.com/eth-brownie/brownie/pull/390))

### Removed
- Source minification ([#384](https://github.com/eth-brownie/brownie/pull/384))

### Fixed
- Recursion errors when a library references itself ([#393](https://github.com/eth-brownie/brownie/pull/393))
- Incorrect source highlights when running tests across multiple projects at once ([#402](https://github.com/eth-brownie/brownie/pull/402))

## [1.6.9](https://github.com/eth-brownie/brownie/tree/v1.6.9) - 2020-04-03
### Fixed
- Encoding bug for lists of tuples
- Allow transfer to unchecksummed hexstring address
- Color output for `dir` in console
- Ignore json files in contracts folder
- `ZeroDivisionError` during coverage evaluation when nothing has changed

## [1.6.8](https://github.com/eth-brownie/brownie/tree/v1.6.8) - 2020-03-30
### Changed
- Use Vyper [v0.1.0-beta17](https://github.com/vyperlang/vyper/releases/tag/v0.1.0-beta.17)

### Fixed
- Bug when determining dependencies of a `Contract` object

## [1.6.7](https://github.com/eth-brownie/brownie/tree/v1.6.7) - 2020-03-09
### Fixed
- `INVALID` instructions with no related ast node (assembly)
- Missing f-strings in compiler output

## [1.6.6](https://github.com/eth-brownie/brownie/tree/v1.6.6) - 2020-03-03
### Changed
- MythX plugin update (PR)[https://github.com/eth-brownie/brownie/pull/365]
- MythX plugin documentation update (PR)[https://github.com/eth-brownie/brownie/pull/366]

## [1.6.5](https://github.com/eth-brownie/brownie/tree/v1.6.5) - 2020-02-19
### Fixed
- Fix issues from missing source offsets in Solidity [v0.6.3](https://github.com/ethereum/solidity/releases/tag/v0.6.3)
- Do not assume pytest will run test functions sequentially (adds support for `-k` flag)

## [1.6.4](https://github.com/eth-brownie/brownie/tree/v1.6.4) - 2020-02-11
### Added
- Show progress spinner when running stateful tests

### Changed
- Update `brownie analyze` based on updates to [MythX](https://www.mythx.io/) API

### Fixed
- Allow import of project `ContractContainer` instances from `brownie` when running tests

## [1.6.3](https://github.com/eth-brownie/brownie/tree/v1.6.3) - 2020-02-09
### Added
- `--stateful` flag to only run or skip stateful test cases
- [EIP-170](https://github.com/ethereum/EIPs/issues/170) size limits: warn on compile, give useful error message on failed deployment

### Changed
- Unexpanded transaction trace is available for deployment transactions

### Fixed
- Warn instead of raising when an import spec cannot be found
- Handle `REVERT` outside of function when generating revert map

## [1.6.2](https://github.com/eth-brownie/brownie/tree/v1.6.2) - 2020-02-05
### Fixed
- Retrieve config file from brownie/data when generating new project

## [1.6.1](https://github.com/eth-brownie/brownie/tree/v1.6.1) - 2020-02-03
### Changed
- Bump dependency versions, notably [web3.py](https://github.com/ethereum/web3.py) [v5.5.0](https://web3py.readthedocs.io/en/stable/releases.html#v5-5-0-2020-02-03) to support the new [ENS registry](https://medium.com/the-ethereum-name-service/ens-registry-migration-bug-fix-new-features-64379193a5a)

## [1.6.0](https://github.com/eth-brownie/brownie/tree/v1.6.0) - 2020-02-02
### Added
- [Hypothesis](https://github.com/HypothesisWorks/hypothesis/tree/master/hypothesis-python) integration for property-based and stateful testing
- `TransactionReceipt.new_contracts` - list of contracts deployed during a contract call
- `TransactionReceipt.internal_transfers` - information on internal ether transfers during a transaction

### Changed
- Refactor `brownie.convert` into sub-modules
- Use `eth_abi.grammar.parse` when formatting contract inputs and outputs
- Replace [`docopt`](https://github.com/docopt/docopt) with [`docopt-ng`](https://github.com/bazaar-projects/docopt-ng) (fixes deprecation warnings)
- `ContractContainer.at` compares actual bytecode to expected, returns `Contract` object if they do not match

### Removed
- Custom color settings in the project config file

### Fixed
- bug preventing `pytest.default_contract_owner` config setting from having any effect
- threading exception when contract deployment fails

## [1.5.1](https://github.com/eth-brownie/brownie/tree/v1.5.1) - 2020-01-21
### Fixed
- Correctly isolate path and nodeid from test cases inside classes
- Allow `""` and `"0x"` when converting to bytes, disallow booleans
- Tests can run from inside a project subfolder
- Preserve pytest `rootdir` when a Brownie project is in a subfolder of a Python project

## [1.5.0](https://github.com/eth-brownie/brownie/tree/v1.5.0) - 2020-01-20
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

## [1.4.2](https://github.com/eth-brownie/brownie/tree/v1.4.2) - 2020-01-10
### Added
- Add Ethereum Classic networks in `brownie-config.yaml`
- Accept `atlantis` and `agharta` as EVM ruleset options in `brownie-config.yaml`

### Changed
- Use Vyper [v0.1.0-beta16](https://github.com/vyperlang/vyper/releases/tag/v0.1.0-beta.16)

### Fixed
- Create `~/.brownie/accounts` when `accounts` commandline interface is called

## [1.4.1](https://github.com/eth-brownie/brownie/tree/v1.4.1) - 2020-01-09
### Changed
- Do not install solc until required for compilation
- Adjust compiler config settings to be less Solidity-centric

### Fixed
- Compiler bug when generating Vyper branch paths
- Permission error when launching Brownie with Ganache already running on OSX

## [1.4.0](https://github.com/eth-brownie/brownie/tree/v1.4.0) - 2020-01-07
### Added
- support for Vyper smart contracts ([v0.1.0-beta15](https://github.com/vyperlang/vyper/releases/tag/v0.1.0-beta.15))
- `brownie accounts` commandline interface

## [1.3.2](https://github.com/eth-brownie/brownie/tree/v1.3.2) - 2020-01-01
### Added
- error message for modulus by zero
- progress bar when installing new version of solc

## [1.3.1](https://github.com/eth-brownie/brownie/tree/v1.3.1) - 2019-12-25
### Added
- better error message for division by zero

### Fixed
- Correctly save minified source offsets in build artifacts
- Coverage evaluation: isolate `active_branches` between jumps

## [1.3.0](https://github.com/eth-brownie/brownie/tree/v1.3.0) - 2019-12-20
### Added
- support for Solidity [v0.6.0](https://github.com/ethereum/solidity/releases/tag/v0.6.0)
- allow `istanbul` as choice for EVM ruleset (default is still `petersburg`)
- allow `dev:` revert comments for `assert` statements
- better error messages when sending ether to nonpayable function, or trying to access an invalid array index

### Fixed
- GUI properly highlights `JUMPDEST` targets within first 256 bytes
- Close IO objects to avoid warnings on exit

## [1.2.1](https://github.com/eth-brownie/brownie/tree/v1.2.1) - 2019-11-28
### Added
- cache available solc compiler versions to avoid repeated calls
- store data files in `~/.brownie/`

### Fixed
- removed Tkinter dependency when not loading the GUI

## [1.2.0](https://github.com/eth-brownie/brownie/tree/v1.2.0) - 2019-11-23
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

## [1.1.0](https://github.com/eth-brownie/brownie/tree/v1.1.0) - 2019-11-04
### Added
- support for Python 3.8

### Changed
- project config files use `YAML` formatting

## [1.0.1](https://github.com/eth-brownie/brownie/tree/v1.0.1) - 2019-10-13
### Fixed
- regex pattern for finding contracts in source
- string formatting in cli
- calling `rpc.attach` with no port set

## [1.0.0](https://github.com/eth-brownie/brownie/tree/v1.0.0) - 2019-09-24
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

## [1.0.0b11](https://github.com/eth-brownie/brownie/tree/v1.0.0b11) - 2019-08-18
- Require web3.py version 5, updates based on breaking changes
- Add support for ABIEncoderV2
- Add Project class, allow opening multiple projects at the same time
- Determine solc version using pragma, allow multiple versions in one project
- Set EVM version in config file
- Allow config file comments, change structure
- Add PublicKeyAccount and Contract (via ABI), allow tracebacks on unknown contracts
- Expanded Alert functionality
- Windows bugfixes

## [1.0.0b10](https://github.com/eth-brownie/brownie/tree/v1.0.0b10) - 2019-07-21
- Use pytest for unit testing
- remove check module, add check.equals comparison logic to ReturnValue
- Modify coverage evaluation to work with pytest
- remove brownie.types package, move classes to related modules
- replace wei function with Wei class, expand functionality
- add EthAddress and HexString helper classes
- improved formatting for tx.traceback and tx.call_trace

## [1.0.0b9](https://github.com/eth-brownie/brownie/tree/v1.0.0b9) - 2019-07-08
- Support for overloaded function names
- Bugfixes
- Minor code changes and improvements

## [1.0.0b8](https://github.com/eth-brownie/brownie/tree/v1.0.0b8) - 2019-06-30
- Rebuild of coverage evaluation functionality using contract ASTs
- Split coverage eval results between branches and statements, add GUI support
- Add tracebacks for failed transactions, better call trace formatting
- Allow contract minification before compiling
- Enable output console in GUI (very basic for now)
- Rebuild brownie console using code.InteractiveConsole
- Significant code refactoring and reorganization
- Emphasis on standardized structure across modules and increased ease of testing
- More tests, coverage at 88%

## [1.0.0b7](https://github.com/eth-brownie/brownie/tree/v1.0.0b7) - 2019-05-24
- Commented dev revert strings
- Custom exception classes
- Standardize contract outputs
- Add Travis and Tox, test coverage at 67%
- Many bugfixes

## [1.0.0b6](https://github.com/eth-brownie/brownie/tree/v1.0.0b6) - 2019-05-14
- Changes to ContractConstructor call arguments
- Bugfixes and minor changes

## [1.0.0b5](https://github.com/eth-brownie/brownie/tree/v1.0.0b5) - 2019-05-13
- Use relative paths in build json files
- Revert calls-as-transactions when evaluating coverage
- Significant refactor and optimizations to coverage analysis
- changes to coverageMap format, add coverageMapTotals
- Save coverage data to reports/ subfolder
- Improvements to GUI

## [1.0.0b4](https://github.com/eth-brownie/brownie/tree/v1.0.0b4) - 2019-05-08
- Add broadcast_reverting_tx flag
- Use py-solc-x 0.4.0
- Detect and attach to an already active RPC client, better verbosity on RPC exceptions
- Introduce Singleton metaclass and refactor code to take advantage
- Add EventDict and EventItem classes for transaction event logs
- cli.color, add _print_as_dict _print_as_list _dir_color attributes
- Add conversion methods in types.convert
- Remove brownie.utils package, move modules to network and project packages
- Bugfixes and minor changes

## [1.0.0b3](https://github.com/eth-brownie/brownie/tree/v1.0.0b3) - 2019-04-26
- major code re-organization and refactoring
- allow skipping contracts with _
- modify test coverage file format
- merge test and coverage components of cli
- only run tests / coverage evaluation if related files have changed
- integrate opview as brownie gui
- many bugfixes and minor changes

## [1.0.0b2](https://github.com/eth-brownie/brownie/tree/v1.0.0b2) - 2019-04-14
- add compile command to cli
- bugfix in pypi package requirements
- show numbers on skipped and failing tests

## [1.0.0b1](https://github.com/eth-brownie/brownie/tree/v1.0.0b1) - 2019-04-11
- major code re-organization, brownie now works as a package and is installable via pip
- remove os.path in favor of pathlib.Path - allow Windows support
- rebuild brownie console, use compile to check for completed statements
- remove Accounts.mnemonic
- transaction.history is now a custom data class
- save and load accounts using standard encrypted keystore files
- add brownie bake to initialize projects from template
- many bugfixes and minor changes

## [0.9.5](https://github.com/eth-brownie/brownie/tree/v0.9.5) - 2019-04-02
- check.true and check.false require booleans to pass
- Allow subfolders within tests/
- Only run specific tests within a file
- More efficient transaction stack trace analysis
- Improvements to compiler efficiency and functionality
- account.transfer accepts data
- add ContractTx.encode_abi
- add ContractContainer.get_method
- Bugfixes

## [0.9.4](https://github.com/eth-brownie/brownie/tree/v0.9.4) - 2019-02-25
- Improved console formatting for lists and dicts
- Run method returns list of scripts when no argument is given
- Do not keep mnemonics and private keys in readline history
- Use KwargTuple type for call return values
- Bugfixes

## [0.9.3](https://github.com/eth-brownie/brownie/tree/v0.9.3) - 2019-02-20
- Raise ValueError when attempting to modify non-existant config settings
- Modify install script
- Minor bugfixes

## [0.9.2](https://github.com/eth-brownie/brownie/tree/v0.9.2) - 2019-02-19
- Add --stable and --dev flags to swap between master and develop branches
- Better verbosity for check.reverts exception string
- Config settings are reset when network resets
- Add default_contract_owner setting

## [0.9.1](https://github.com/eth-brownie/brownie/tree/v0.9.1) - 2019-02-18
- Add --always-transact flag for test and coverage
- Do not show individual methods when contract coverage is 0%
- Minor bugfixes

## [0.9.0](https://github.com/eth-brownie/brownie/tree/v0.9.0) - 2019-02-16
- Initial release
