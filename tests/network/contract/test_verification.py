import solcx


def test_verification_info(testproject):
    ImportTester = testproject.ImportTester
    input_data = ImportTester.get_verification_info()["standard_json_input"]

    # output selection isn't included in the verification info because
    # etherscan replaces it regardless. Here we just replicate with what they
    # would include
    input_data["settings"]["outputSelection"] = {
        "*": {"*": ["evm.bytecode", "evm.deployedBytecode", "abi"]}
    }

    compiler_version, _ = ImportTester._build["compiler"]["version"].split("+")
    output_data = solcx.compile_standard(input_data, solc_version=compiler_version)
    # keccak256 = 0xd61b13a841b15bc814760b36086983db80788946ca38aa90a06bebf287a67205
    build_info = output_data["contracts"]["ImportTester.sol"]["ImportTester"]

    assert build_info["abi"] == ImportTester.abi
    # ignore the metadata at the end of the bytecode, etherscan does the same
    assert build_info["evm"]["bytecode"]["object"][:-96] == ImportTester.bytecode[:-96]
    assert (
        build_info["evm"]["deployedBytecode"]["object"][:-96]
        == ImportTester._build["deployedBytecode"][:-96]
    )
