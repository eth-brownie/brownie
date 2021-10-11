def test_verification_info(BrownieTester, brownie_tester_flat):
    v = BrownieTester.get_verification_info()
    assert v["contract_name"] == "BrownieTester"
    assert v["compiler_version"].startswith("0.5.")
    assert v["optimizer_enabled"] is True
    assert v["optimizer_runs"] == 200
    assert v["license_identifier"] == "NONE"
    assert v["bytecode_len"] == 9842

    # skip version pragma, because it is inconsistent
    # new line formatting and etc. ....
    # assert v["flattened_source"][58:] == brownie_tester_flat[58:]
