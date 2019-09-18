#!/usr/bin/python3

from brownie.project import compile_source, sources


def test_minify(btsource):
    minified, offsets = sources.minify(btsource)
    assert minified != btsource
    assert "contract BrownieTester{" in minified
    assert "contract ExternalCallTester{" in minified


def test_minify_compiles(solc5source):
    foo = compile_source(solc5source, solc_version="0.5.7")["Foo"]
    minified, _ = sources.minify(solc5source)
    minifoo = compile_source(minified, solc_version="0.5.7")["Foo"]
    assert foo._build["bytecodeSha1"] == minifoo._build["bytecodeSha1"]
    assert foo._build["source"] != minifoo._build["source"]


def test_expand_offset(btsource, BrownieTester):
    minified, _ = sources.minify(btsource)
    expanded = BrownieTester._project._sources.expand_offset(
        "BrownieTester", (minified.index("contract"), minified.index("contract") + 7)
    )
    assert btsource.index("contract"), btsource.index("contract") + 7 == expanded
