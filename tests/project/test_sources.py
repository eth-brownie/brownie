#!/usr/bin/python3

from brownie.project import sources


def _solc_5_source():
    source = sources.get('BrownieTester')
    source = source.replace('BrownieTester', 'TempTester')
    source = source.replace('UnlinkedLib', 'TestLib')
    return source


def _solc_4_source():
    source = _solc_5_source()
    source = source.replace('payable ', '')
    source = source.replace('^0.5.0', '^0.4.25')
    return source


def test_unlinked_libraries():
    source = _solc_5_source()
    build_json = sources.compile_source(source, solc_version="0.5.7")
    assert '__TestLib__' in build_json['TempTester']['bytecode']
    source = _solc_4_source()
    build_json = sources.compile_source(source, solc_version="0.4.25")
    assert '__TestLib__' in build_json['TempTester']['bytecode']


def test_minify():
    source = sources.get('BrownieTester')
    minified, offsets = sources.minify(source)
    assert minified != source
    assert "contract BrownieTester{" in minified
    assert "library UnlinkedLib{" in minified


def test_minify_compiles():
    source = _solc_5_source()
    build_json = sources.compile_source(source, solc_version="0.5.7")['TempTester']
    minified, _ = sources.minify(source)
    minified_build = sources.compile_source(minified, solc_version="0.5.7")['TempTester']
    assert build_json['bytecodeSha1'] == minified_build['bytecodeSha1']
    assert build_json['source'] != minified_build['source']


def test_expand_offset():
    source = sources.get('BrownieTester')
    minified, _ = sources.minify(source)
    expanded = sources.expand_offset(
        "BrownieTester",
        (minified.index("contract"), minified.index("contract")+7)
    )
    assert source.index("contract"), source.index("contract")+7 == expanded
