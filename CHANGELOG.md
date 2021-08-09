# CHANGELOG

All notable changes to this project are documented in this file.

This changelog format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased](https://github.com/eth-brownie/brownie)

## [1.16.0](https://github.com/eth-brownie/brownie/tree/v1.16.0) - 2021-08-08
### Added
- Initial support for [Hardhat Network](https://hardhat.org/hardhat-network/) as an alternative to Ganache ([#1043](https://github.com/eth-brownie/brownie/pull/1043))
- Support for [EIP-1559](https://eips.ethereum.org/EIPS/eip-1559) transactions ([#1179](https://github.com/eth-brownie/brownie/pull/1179))
- Added `LocalAccount.sign_defunct_message` method to sign `EIP-191` text messages ([#1163](https://github.com/eth-brownie/brownie/pull/1163))

### Fixed
-Preserve active input when writing to the console ([#1181](https://github.com/eth-brownie/brownie/pull/1181))
-Modifications to internal flow when handling transactions, fixes some threadlock issues ([#1182](https://github.com/eth-brownie/brownie/pull/1182))

## [1.15.2](https://github.com/eth-brownie/brownie/tree/v1.15.2) - 2021-07-26
### Fixed
- Bump `py-solc-ast` version to fix AST issues with solc `>=0.8.3` ([#1165](https://github.com/eth-brownie/brownie/pull/1165))

## [1.15.1](https://github.com/eth-brownie/brownie/tree/v1.15.1) - 2021-07-23
### Fixed
- Bugfix with caching `eth_sendTransaction` and related RPC calls ([#1160](https://github.com/eth-brownie/brownie/pull/1160))

## [1.15.0](https://github.com/eth-brownie/brownie/tree/v1.15.0) - 2021-07-22
### Added
- Add support remapping with a sub-folder (like OpenZeppelin/openzeppelin-contracts-upgradeable, ref: [#1137](https://github.com/eth-brownie/brownie/issues/1137))
- Add polygon network integration ([#1119](https://github.com/eth-brownie/brownie/pull/1119))
- Add support for `POLYGONSCAN_TOKEN` env var ([#1135](https://github.com/eth-brownie/brownie/pull/1135))
- Add Multicall context manager ([#1125](https://github.com/eth-brownie/brownie/pull/1125))
- Add initial support for Solidity 0.8's typed errors ([#1110](https://github.com/eth-brownie/brownie/pull/1110))
- Add xdai network integration ([#1136](https://github.com/eth-brownie/brownie/pull/1136))
- Added `LocalAccount.sign_message` method to sign `EIP712Message` objects ([#1097](https://github.com/eth-brownie/brownie/pull/1097))
- Accept password as a kwarg in `Account.load` ([#1099](https://github.com/eth-brownie/brownie/pull/1099))
- Basic support for clef as an account manager (allows hardware wallets) ([#1104](https://github.com/eth-brownie/brownie/pull/1104))
- Updates to support Vyper `v0.2.14` ([#1155](https://github.com/eth-brownie/brownie/pull/1155))

### Fixed
- Fixed subcalls to empty accounts not appearing in the subcalls property of `TransactionReceipts` ([#1106](https://github.com/eth-brownie/brownie/pull/1106))
- Alert message bug ([#1094](https://github.com/eth-brownie/brownie/pull/1094))
- Do not assume latest nonce is highest nonce when handling multiple pending tx's ([#1098](https://github.com/eth-brownie/brownie/pull/1098))
- Accept `Wei` objects in gas strategies ([#1113](https://github.com/eth-brownie/brownie/pull/1113))
- Do not warn when using `no_call_coverage` as a pytest mark ([#1150](https://github.com/eth-brownie/brownie/pull/1150))

## [1.14.6](https://github.com/eth-brownie/brownie/tree/v1.14.6) - 2021-04-20
### Changed
- Upgraded web3 dependency to version 5.18.0 ([#1064](https://github.com/eth-brownie/brownie/pull/1064))
- Upgraded pytest dependency to version 6.2.3 ([#1065](https://github.com/eth-brownie/brownie/pull/1065))
- Upgraded hypothesis dependency to version 6.10.0 ([#1066](https://github.com/eth-brownie/brownie/pull/1066))

### Fixed
- Issue with `BSCSCAN_TOKEN` ([#1062](https://github.com/eth-brownie/brownie/pull/1062))
- Correctly load `.env` values ([#1063](https://github.com/eth-brownie/brownie/pull/1063))

## [1.14.5](https://github.com/eth-brownie/brownie/tree/v1.14.5) - 2021-04-16
### Added
- Added documentation detailing how private Github repositories can be used as a package installation source.
- Add passphrase kwarg to `Account.from_mnemonic` ([#1050](https://github.com/eth-brownie/brownie/pull/1050))

### Changed
- Include `chainId` field when signing transactions ([#1056](https://github.com/eth-brownie/brownie/pull/1056))

### Fixed
- Fixed a formatting issue on the new [environment variable section](https://eth-brownie.readthedocs.io/en/stable/config.html?highlight=POSIX-style#variable-expansion) ([#1038](https://github.com/eth-brownie/brownie/pull/1038))
- Fixed Github package installation failing for private repositories ([#1055](https://github.com/eth-brownie/brownie/pull/1055)).
- Adjusted Github API token error message so that it correctly emits when auth failure occurs ([#1052](https://github.com/eth-brownie/brownie/pull/1052))
- Remove `__ret_value__` prior to writing console output ([#1057](https://github.com/eth-brownie/brownie/pull/1057))
- Handle missing contract when generating transaction receipt ([#1058](https://github.com/eth-brownie/brownie/pull/1058))
- `StopIteration` issues within receipts ([#1059](https://github.com/eth-brownie/brownie/pull/1059))
- Do not cache `eth_newBlockFilter` ([#1061](https://github.com/eth-brownie/brownie/pull/1061))

## [1.14.4](https://github.com/eth-brownie/brownie/tree/v1.14.4) - 2021-04-05
### Added
- Support for environment variables in brownie config ([#1012](https://github.com/eth-brownie/brownie/pull/1012))
- Add Fantom to default networks ([#980](https://github.com/eth-brownie/brownie/pull/980))

### Changed
- Gas report also shows average price for only confirmed txs ([#1020](https://github.com/eth-brownie/brownie/pull/1020))

### Fixed
- Add project to brownie namespace within console ([#1029](https://github.com/eth-brownie/brownie/pull/1029))
- Balance contract member override ([#1030](https://github.com/eth-brownie/brownie/pull/1030))
- Correct frame in pytest interactive debug mode ([#1034](https://github.com/eth-brownie/brownie/pull/1034))

## [1.14.3](https://github.com/eth-brownie/brownie/tree/v1.14.3) - 2021-03-27
### Added
- Support for `BSCSCAN_TOKEN` env var ([#1017](https://github.com/eth-brownie/brownie/pull/1017))

### Fixed
- Ensure node client supports filters before enabling caching middleware ([#1009](https://github.com/eth-brownie/brownie/pull/1009))
- Support `abicoder v2` pragma when verifying source code ([#1018](https://github.com/eth-brownie/brownie/pull/1018))

## [1.14.2](https://github.com/eth-brownie/brownie/tree/v1.14.2) - 2021-03-20
### Fixed
- Attaching to dockerized RPC-clients works on OSX without sudo ([#995](https://github.com/eth-brownie/brownie/pull/995))
- Bug when calling `chain.mine` without a timestamp ([#1005](https://github.com/eth-brownie/brownie/pull/1005))

## [1.14.1](https://github.com/eth-brownie/brownie/tree/v1.14.1) - 2021-03-19
### Fixed
- Improve logic around `eth_getCode` caching to consider selfdestruct via delegate call ([#1002](https://github.com/eth-brownie/brownie/pull/1002))
- Standardize process of adding middlewares upon connection ([#1001](https://github.com/eth-brownie/brownie/pull/1001))

## [1.14.0](https://github.com/eth-brownie/brownie/tree/v1.14.0) - 2021-03-18
### Added
- Generalized RPC logic allowing (limited) use of `geth --dev` as a local test network ([#998](https://github.com/eth-brownie/brownie/pull/998))
- RPC call caching via web3 middleware ([#997](https://github.com/eth-brownie/brownie/pull/997))
- Allow tests to target project outside the current working directory via `--brownie-project` cli flag ([#996](https://github.com/eth-brownie/brownie/pull/996))
- Add BSC mainnet and fork-mode to default networks ([#961](https://github.com/eth-brownie/brownie/pull/961))

### Changed
- `export BROWNIE_LIB=1` to install brownie with soft pins. Also ensured hard pins for all dependencies are set. ([#993](https://github.com/eth-brownie/brownie/pull/993))

## [1.13.4](https://github.com/eth-brownie/brownie/tree/v1.13.4) - 2021-03-14
### Added
- Detect EIP-1167 and Vyper minimal proxies ([#984](https://github.com/eth-brownie/brownie/pull/984))
- Decode ds-note events ([#985](https://github.com/eth-brownie/brownie/pull/985))

### Changed
- During pytest interactive debugging , `continue` now exits the console to run the next test ([#989](https://github.com/eth-brownie/brownie/pull/989))

### Fixed
- Issue around the "optimizer revert" in solidity 0.8.2 ([#988](https://github.com/eth-brownie/brownie/pull/988))

## [1.13.3](https://github.com/eth-brownie/brownie/tree/v1.13.3) - 2021-03-08
### Added
- Option to choose console editting mode ([#970](https://github.com/eth-brownie/brownie/pull/970))

### Fixed
- Strip whitespace from `address_or_alias` ([#978](https://github.com/eth-brownie/brownie/pull/978))
- Automatic source code verification on BscScan ([#962](https://github.com/eth-brownie/brownie/pull/962))
- Heuristic for nonpayable function revert in Vyper `v0.2.11` ([#979](https://github.com/eth-brownie/brownie/pull/979))

## [1.13.2](https://github.com/eth-brownie/brownie/tree/v1.13.2) - 2021-02-28
### Added
- Load installed packages via `project.load` ([#971](https://github.com/eth-brownie/brownie/pull/971))

### Changed
- `brownie run --interactive` enters the console with the namespace of the successfully executed function ([#976](https://github.com/eth-brownie/brownie/pull/976))

### Fixed
- Bump dependency version for [eth-event](https://github.com/iamdefinitelyahuman/eth-event) to [1.2.1](https://github.com/iamdefinitelyahuman/eth-event/releases/tag/v1.2.1) to mitigate the topic generation bug for events with dynamic/fixed size tuple array inputs ([#957](https://github.com/eth-brownie/brownie/pull/957))
- Iterate over network connections instead of local process list to support RPC-attaching with host-based and dockerized RPC clients ([#972](https://github.com/eth-brownie/brownie/pull/972))
- Resolve hostnames provided in host network field to the actual IP when RPC-attaching ([#972](https://github.com/eth-brownie/brownie/pull/972))
- Correctly handle non-push instructions when parsing compiler outputs ([#952](https://github.com/eth-brownie/brownie/pull/952))
- Issue with implementation contract addresses pulled from `eth_getStorageAt` using Ganache `v6.12.2` ([#974](https://github.com/eth-brownie/brownie/pull/974))

## [1.13.1](https://github.com/eth-brownie/brownie/tree/v1.13.1) - 2021-01-31
### Fixed
- Verify that instruction is `PUSH` before popping pushed bytes ([#935](https://github.com/eth-brownie/brownie/pull/935))
- Handle empty return value from `eth_getStorageAt` ([#946](https://github.com/eth-brownie/brownie/pull/946))
- Do not decode event logs immediately ([#947](https://github.com/eth-brownie/brownie/pull/947))

## [1.13.0](https://github.com/eth-brownie/brownie/tree/v1.13.0) - 2021-01-09
### Added
- Automatic source code verification on Etherscan ([#914](https://github.com/eth-brownie/brownie/pull/914))
- Allow replacing transactions that were broadcasted outside of Brownie ([#922](https://github.com/eth-brownie/brownie/pull/922))
- Add `decode_input`, `decode_output` and `info` methods to `OverloadedMethod` object ([#925](https://github.com/eth-brownie/brownie/pull/925))

### Changed
- Lazily decode events for confirmed transactions ([#926](https://github.com/eth-brownie/brownie/pull/926))

## [1.12.4](https://github.com/eth-brownie/brownie/tree/v1.12.4) - 2021-01-03
### Changed
- Use `ReturnType` instead of `list` for some `_EventItem` return values ([#919](https://github.com/eth-brownie/brownie/pull/919))
- Only decode events in reverting transactions upon request ([#920](https://github.com/eth-brownie/brownie/pull/920))
### Fixed
- Correctly handle malformed calldata in subcalls ([#913](https://github.com/eth-brownie/brownie/pull/913))
- Brownie bake uses the default branch instead of assuming `master` ([#917](https://github.com/eth-brownie/brownie/pull/917))

## [1.12.3](https://github.com/eth-brownie/brownie/tree/v1.12.3) - 2020-12-26
### Added
- Exposed `chain_id` and `network_id` ganache-cli parameters. Forked networks retain `chain_id`. ([#908](https://github.com/eth-brownie/brownie/pull/908))
- Show more information about events in `TransactionReceipt.info` ([#898](https://github.com/eth-brownie/brownie/pull/898))
- Support for Solidity error codes ([#906](https://github.com/eth-brownie/brownie/pull/906))
- `TxHistory.wait` to wait for all pending transactions ([#910](https://github.com/eth-brownie/brownie/pull/910))

### Fixed
- Handle missing source nodes due to Yul optimizer ([#895](https://github.com/eth-brownie/brownie/pull/895))
- Typo in link to mixes ([#886](https://github.com/eth-brownie/brownie/pull/886))
- Fixes for tracebacks and dev revert strings in Solidity 0.8.x ([#907](https://github.com/eth-brownie/brownie/pull/907))
- Console output for automatically repriced transactions ([#909](https://github.com/eth-brownie/brownie/pull/909))

## [1.12.2](https://github.com/eth-brownie/brownie/tree/v1.12.2) - 2020-12-04
### Added
- Detect EIP1822 proxies `Contract.from_explorer` ([#881](https://github.com/eth-brownie/brownie/pull/881))
- Support for [EIP 1967](https://eips.ethereum.org/EIPS/eip-1967) proxy pattern in `Contract.from_explorer` ([#876](https://github.com/eth-brownie/brownie/pull/876))
- `ContractContainer.decode_input` ([#879](https://github.com/eth-brownie/brownie/pull/879))

### Changed
- Build artifacts for dependencies are now saved at `build/contracts/dependencies` ([#878](https://github.com/eth-brownie/brownie/pull/878))

### Fixed
- Ensure receiver address is checksummed when calling `eth_estimateGas` ([#880](https://github.com/eth-brownie/brownie/pull/880))

## [1.12.1](https://github.com/eth-brownie/brownie/tree/v1.12.1) - 2020-11-28
### Fixed
- Append zero-bytes when expected size of memory exceeds actual size ([#868](https://github.com/eth-brownie/brownie/pull/868))

## [1.12.0](https://github.com/eth-brownie/brownie/tree/v1.12.0) - 2020-11-24
### Added
- `TransactionReceipt.replace` for rebroadcasting pending transactions ([#846](https://github.com/eth-brownie/brownie/pull/846))
- Gas strategies for automatic transaction pricing and replacement ([#847](https://github.com/eth-brownie/brownie/pull/847))
- Allow broadcasting reverting transactions in a live environment ([#854](https://github.com/eth-brownie/brownie/pull/854))
- Add `timedelta` as a kwarg in `chain.mine` ([#856](https://github.com/eth-brownie/brownie/pull/856))
- `require_network` pytest marker ([#858](https://github.com/eth-brownie/brownie/pull/858))
- `TransactionReceipt.dev_revert_msg` to access the dev revert string when there is a regular revert message ([#860](https://github.com/eth-brownie/brownie/pull/860))
- Allow targetting dev revert string in `brownie.reverts` ([#861](https://github.com/eth-brownie/brownie/pull/861))
- Support regex in `brownie.reverts` ([#864](https://github.com/eth-brownie/brownie/pull/864))

### Changed
- Improved handling of trace queries and related exceptions ([#853](https://github.com/eth-brownie/brownie/pull/853))
- Disallow assignment over contract functions ([#855](https://github.com/eth-brownie/brownie/pull/855))
- `skip_coverage` and `no_call_coverage` are now markers, the fixtures have been deprecated ([#859](https://github.com/eth-brownie/brownie/pull/859))
- Improved exception messages for contract calls missing the `"from"` field ([864](https://github.com/eth-brownie/brownie/pull/865))

### Fixed
- Address resolution in `Contract.at` ([#842](https://github.com/eth-brownie/brownie/pull/842))
- Handle undecodable revert messages within subcalls ([#843](https://github.com/eth-brownie/brownie/pull/843))
- Bug when installed packages contain an `interfaces` folder ([#857](https://github.com/eth-brownie/brownie/pull/857))

## [1.11.12](https://github.com/eth-brownie/brownie/tree/v1.11.12) - 2020-11-04
### Added
- `timestamp` kwarg for `chain.mine` ([#838](https://github.com/eth-brownie/brownie/pull/838))
- `ETH_ADDRESS` constant ([#835](https://github.com/eth-brownie/brownie/pull/835))
- show nonce in console output for pending transactions ([#833](https://github.com/eth-brownie/brownie/pull/833))

### Fixed
- Allow use of `ProjectContract` in tx "from" field on development networks ([#836](https://github.com/eth-brownie/brownie/pull/836))
- Do not attempt to open debugging console when the failing test has not been collected due to a `SyntaxError` ([#834](https://github.com/eth-brownie/brownie/pull/834))

## [1.11.11](https://github.com/eth-brownie/brownie/tree/v1.11.11) - 2020-10-31
### Added
- `ZERO_ADDRESS` constant is now available from main namespace ([#830](https://github.com/eth-brownie/brownie/pull/830))
- Include nonce in `stdout` output when broadcasting a transaction ([#833](https://github.com/eth-brownie/brownie/pull/833))

### Changed
- `brownie bake` project names are no longer case sensetive ([#829](https://github.com/eth-brownie/brownie/pull/829))

### Fixed
- Handle `str` when looking at traceback paths ([#823](https://github.com/eth-brownie/brownie/pull/823))
- Add `__ne__` to `ReturnValue` object ([#831](https://github.com/eth-brownie/brownie/pull/831))

## [1.11.10](https://github.com/eth-brownie/brownie/tree/v1.11.10) - 2020-10-23
### Changed
- During testing, do not connect to network until immediately before running tests ([#819](https://github.com/eth-brownie/brownie/pull/819))

### Fixed
- Vyper 0.2.5 non-payable revert error no longer displays the entire contract ([#812](https://github.com/eth-brownie/brownie/pull/812))
- Handle correct `ConnectionError` when pulling Vyper versions ([#815](https://github.com/eth-brownie/brownie/pull/815))
- Typo in `gasPrice` during gas estimation ([#817](https://github.com/eth-brownie/brownie/pull/817))
- Handle `0x` when parsing tuples with black for call trace ([#818](https://github.com/eth-brownie/brownie/pull/818))
- Console completions for `Contract.deploy` ([#820](https://github.com/eth-brownie/brownie/pull/820))

## [1.11.9](https://github.com/eth-brownie/brownie/tree/v1.11.9) - 2020-10-11
### Added
- `TxHistory.filter` method ([#804](https://github.com/eth-brownie/brownie/pull/804))
- Allow force-compiling of specific contracts in CLI ([#802](https://github.com/eth-brownie/brownie/pull/802))

### Fixed
- Include `vyper` library version in installed versions, after installing a new version ([#803](https://github.com/eth-brownie/brownie/pull/803))
- Understand `Contract` objects in the `from` field of a transaction dict ([#801](https://github.com/eth-brownie/brownie/pull/801))

## [1.11.8](https://github.com/eth-brownie/brownie/tree/v1.11.8) - 2020-10-07
### Added
- Automatically add `tx` as a local variable during interactive debugging ([#796](https://github.com/eth-brownie/brownie/pull/796))

### Changed
- Gas buffer is not applied to transactions between EOAs ([#798](https://github.com/eth-brownie/brownie/pull/798))
- Use `vyper` instead of `vvm` for compilation, where possible ([#797](https://github.com/eth-brownie/brownie/pull/797))

### Fixed
- Correctly highlight skipped, previously failing tests in red when using `-U` flag ([#795](https://github.com/eth-brownie/brownie/pull/795))

## [1.11.7](https://github.com/eth-brownie/brownie/tree/v1.11.7) - 2020-10-02
### Added
- Support for Etherscan's multi-file source output ([#786](https://github.com/eth-brownie/brownie/pull/786))
- Improvements to console hinting and autocompletion ([#788](https://github.com/eth-brownie/brownie/pull/788))

### Changed
- Bump suggested Ganache version to `v6.11.0` ([#787](https://github.com/eth-brownie/brownie/pull/787))

### Fixed
- Update non-payable heuristic for Vyper `v0.2.5` ([#784](https://github.com/eth-brownie/brownie/pull/784))

## [1.11.6](https://github.com/eth-brownie/brownie/tree/v1.11.6) - 2020-09-26
### Added
- `Account.get_deployment_address` ([#763](https://github.com/eth-brownie/brownie/pull/763))
- Use `eth_unlockUnkonwnAccount` to unlock arbitrary accounts in development mode ([#776](https://github.com/eth-brownie/brownie/pull/776))

### Changed
- Generalize `sys.argv` handling for `brownie test` to allow arbitrary flags ([#773](https://github.com/eth-brownie/brownie/pull/773))
- Disable `stdout` capture when compiling a project prior to running tests ([#774](https://github.com/eth-brownie/brownie/pull/774))
- Attempt to determine proxy implementation without relying on Etherscan APi output ([#777](https://github.com/eth-brownie/brownie/pull/777))

### Fixed
- Add `gas_limit` kwarg for `Account.estimate_gas` ([#764](https://github.com/eth-brownie/brownie/pull/764))
- Improve exception message on bytecode exceeding 24kb limit ([#767](https://github.com/eth-brownie/brownie/pull/767))
- Properly handle no installed compiler when using `compile_source` ([#768](https://github.com/eth-brownie/brownie/pull/768))

## [1.11.5](https://github.com/eth-brownie/brownie/tree/v1.11.5) - 2020-09-16
### Changed
- `EthAddress` is now hashable ([#756](https://github.com/eth-brownie/brownie/pull/756))
- Warn instead of raising when an event has an incorrect number of topics ([#759](https://github.com/eth-brownie/brownie/pull/759))

### Fixed
- More trace fixes ([#760](https://github.com/eth-brownie/brownie/pull/760))

## [1.11.4](https://github.com/eth-brownie/brownie/tree/v1.11.4) - 2020-09-13
### Added
- Default interfaces in `InterfaceContainer` ([#754](https://github.com/eth-brownie/brownie/pull/754))
- `--size` flag for `brownie compile` to see deployed bytecode sizes ([#750](https://github.com/eth-brownie/brownie/pull/750))

### Changed
- Improve error message for `AttributeError` from `ProjectContract` ([#753](https://github.com/eth-brownie/brownie/pull/753))

### Fixed
- Check min solc version when using `Contract.from_explorer` ([#752](https://github.com/eth-brownie/brownie/pull/752))
- Issues related to interfaces and contracts using the same name ([#751](https://github.com/eth-brownie/brownie/pull/751))

## [1.11.3](https://github.com/eth-brownie/brownie/tree/v1.11.3) - 2020-09-11
### Added
- `InterfaceConstructor.selectors` ([#748](https://github.com/eth-brownie/brownie/pull/748))

### Fixed
- Ensure `VirtualMachineError.__str__` always returns a string ([#747](https://github.com/eth-brownie/brownie/pull/747))
- Expanding traces when the contract is unknown ([#745](https://github.com/eth-brownie/brownie/pull/745))

## [1.11.2](https://github.com/eth-brownie/brownie/tree/v1.11.2) - 2020-09-07
### Added
- `chain.new_blocks` for iterating over new blocks ([#742](https://github.com/eth-brownie/brownie/pull/742))

### Fixed
- Various fixes involving transaction traces and subcalls ([#741](https://github.com/eth-brownie/brownie/pull/741))

## [1.11.1](https://github.com/eth-brownie/brownie/tree/v1.11.1) - 2020-09-06
### Added
- `gas_buffer` setting for transactions ([#739](https://github.com/eth-brownie/brownie/pull/739))

### Fixed
- Formatting issue when expanding call traces ([#737](https://github.com/eth-brownie/brownie/pull/737))

## [1.11.0](https://github.com/eth-brownie/brownie/tree/v1.11.0) - 2020-08-28
### Added
- Support for multiple Vyper versions ([#731](https://github.com/eth-brownie/brownie/pull/731))

### Changed
- Use `solcx` v1.0.0 ([#733](https://github.com/eth-brownie/brownie/pull/733))
- Always enter console when using `brownie run -I` ([#732](https://github.com/eth-brownie/brownie/pull/732))
- Allow namespace collisions between interfaces ([#734](https://github.com/eth-brownie/brownie/pull/734))

### Fixed
- Ignore `TempProject` contracts when calculating coverage ([#730](https://github.com/eth-brownie/brownie/pull/730))

## [1.10.6](https://github.com/eth-brownie/brownie/tree/v1.10.6) - 2020-08-18
### Changed
- Warn instead of raising when contract has a `balance` function ([#721](https://github.com/eth-brownie/brownie/pull/721))
- `brownie run` can run scripts outside of projects ([#722](https://github.com/eth-brownie/brownie/pull/722))

### Fixed
- Allow using contract types in conftest ([#719](https://github.com/eth-brownie/brownie/pull/719))

## [1.10.5](https://github.com/eth-brownie/brownie/tree/v1.10.5) - 2020-08-07
### Changed
- Container repr outside of console ([#707](https://github.com/eth-brownie/brownie/pull/707))

### Fixed
- Do not shift gas values for `ganache-cli>=6.10.1` ([#704](https://github.com/eth-brownie/brownie/pull/714))
- Handle multiple pragma statements in a single source ([#708](https://github.com/eth-brownie/brownie/pull/708))
- Do not call undo on general exceptions during call-as-tx ([#713](https://github.com/eth-brownie/brownie/pull/713))
- Correctly handle structs and enums outside of contracts ([#715](https://github.com/eth-brownie/brownie/pull/715))

## [1.10.4](https://github.com/eth-brownie/brownie/tree/v1.10.4) - 2020-07-30
### Added
- `--version` cli flag ([#705](https://github.com/eth-brownie/brownie/pull/705))

### Fixed
- Do not mutate hypothesis settings ([#704](https://github.com/eth-brownie/brownie/pull/704))

## [1.10.3](https://github.com/eth-brownie/brownie/tree/v1.10.3) - 2020-07-20
### Changed
- Do not show stateful spinner when stdout is not suppressed ([#696](https://github.com/eth-brownie/brownie/pull/696))

### Fixed
- Decoding error with internal revert message ([#697](https://github.com/eth-brownie/brownie/pull/697))
- Transaction verbosity during tests ([#695](https://github.com/eth-brownie/brownie/pull/695))
- Check for `__getitem__`/`__call__` prior to showing type hints ([#694](https://github.com/eth-brownie/brownie/pull/694))

## [1.10.2](https://github.com/eth-brownie/brownie/tree/v1.10.2) - 2020-07-18
### Fixed
- Decoding error on internal call to an invalid function in a known contract ([#691](https://github.com/eth-brownie/brownie/pull/691))
- `chain.redo` across multiple transactions ([#692](https://github.com/eth-brownie/brownie/pull/692))

## [1.10.1](https://github.com/eth-brownie/brownie/tree/v1.10.1) - 2020-07-17
### Fixed
- `chain` fixture returns expected object ([#689](https://github.com/eth-brownie/brownie/pull/689))

## [1.10.0](https://github.com/eth-brownie/brownie/tree/v1.10.0) - 2020-07-16
### Added
- `TransactionReceipt.call_trace` includes inputs and return values ([#679](https://github.com/eth-brownie/brownie/pull/679))
- `chain` object ([#681](https://github.com/eth-brownie/brownie/pull/681))
- `--silent` flag for `brownie run` ([#680](https://github.com/eth-brownie/brownie/pull/680))
- `address` member for decoded events ([#682](https://github.com/eth-brownie/brownie/pull/682))

### Changed
- Various `rpc` methods have been deprecated in favor of the new `chain` object ([#681](https://github.com/eth-brownie/brownie/pull/681))
- Improvements to console autocompletion / type hints ([#683](https://github.com/eth-brownie/brownie/pull/683))

### Fixed
- Properly handle Solidity source maps that are too long ([#684](https://github.com/eth-brownie/brownie/pull/684))

## [1.9.8](https://github.com/eth-brownie/brownie/tree/v1.9.8) - 2020-07-09
### Added
- Syntax highlights for Vyper exceptions ([#668](https://github.com/eth-brownie/brownie/pull/668))
- Syntax highlights for Solidity exceptions ([#675](https://github.com/eth-brownie/brownie/pull/675))

### Fixed
- Infinite loop when querying implementation contract from Etherscan ([#672](https://github.com/eth-brownie/brownie/pull/672))
- Check return status before streaming brownie mix ([#673](https://github.com/eth-brownie/brownie/pull/673))
- Meaningful error message on failed trace ([#674](https://github.com/eth-brownie/brownie/pull/674))
- Handle incomplete Solidity source map ([#676](https://github.com/eth-brownie/brownie/pull/676))

## [1.9.7](https://github.com/eth-brownie/brownie/tree/v1.9.7) - 2020-07-05
### Added
- `max` gas limit configuration setting ([#664](https://github.com/eth-brownie/brownie/pull/664))
- `--failfast` flag for hypothesis tests ([#666](https://github.com/eth-brownie/brownie/pull/666))

### Fixed
- Iterate trace in reverse when looking for revert reason ([#663](https://github.com/eth-brownie/brownie/pull/663))
- `TransactionReceipt` verbosity and minor fixes ([#665](https://github.com/eth-brownie/brownie/pull/665))

## [1.9.6](https://github.com/eth-brownie/brownie/tree/v1.9.6) - 2020-07-04
### Changed
- Reduce length of traceback on failed Vyper compilation ([#661](https://github.com/eth-brownie/brownie/pull/661))
- Run calls as transactions when catching dev revert string ([#659](https://github.com/eth-brownie/brownie/pull/659))

### Fixed
- Do not reset local chain when closing Brownie ([#660](https://github.com/eth-brownie/brownie/pull/660))

## [1.9.5](https://github.com/eth-brownie/brownie/tree/v1.9.5) - 2020-07-03
### Changed
- Support for Vyper `v0.2.1` ([#656](https://github.com/eth-brownie/brownie/pull/656))
- Updated development network config to match mainnet's latest gas limits ([#650](https://github.com/eth-brownie/brownie/pull/650))

### Fixed
- Heuristic for non-payable function reverts based on changes in Solidity `v0.6.9` ([#647](https://github.com/eth-brownie/brownie/pull/647))
- `brownie run` exit status when using `--interactive` flag ([#655](https://github.com/eth-brownie/brownie/pull/655))

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
