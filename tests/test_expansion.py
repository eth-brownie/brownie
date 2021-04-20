import unittest
import uuid

from brownie._expansion import expand_posix_vars


class TestExpandDict(unittest.TestCase):
    def setUp(self):
        self.v = str(uuid.uuid4())
        self.input = {
            "non": "b",
            "simple": "${FOO}",
            "partial": "the ${FOO}",
            "number": 1,
            "bool": True,
            "nested": {
                "one": "nest ${FOO}",
                "super_nested": {"two": "real ${FOO}", "three": "not"},
            },
            "${A}": "abc",
            "default_envvar_present": "${FOO:-xyz}",
            "default_envvar_missing": "${ABC:-bar}",
            "default_int_present": "${NUM:-42}",
            "default_int_missing": "${ABC:-42}",
            "arr": [{"a": False, "b": False}, {"a": True, "b": "${FOO}"}],
        }
        variables = {"FOO": self.v, "NUM": 314}
        self.res = expand_posix_vars(
            self.input,
            variables,
        )

    def test_basic_string(self):
        assert self.res["non"] == "b"

    def test_simple_expansion(self):
        assert self.res["simple"] == self.v

    def test_partial_string_expansion(self):
        assert self.res["partial"] == f"the {self.v}"

    def test_number(self):
        assert self.res["number"] == 1

    def test_bool(self):
        assert self.res["bool"] == True  # noqa: E712

    def test_nested_partial_string(self):
        assert self.res["nested"]["one"] == f"nest {self.v}"

    def test_double_nested_partial_string(self):
        assert self.res["nested"]["super_nested"]["two"] == f"real {self.v}"

    def test_double_nested_plain(self):
        assert self.res["nested"]["super_nested"]["three"] == "not"

    def test_variable_name_not_expanded(self):
        assert self.res["${A}"] == "abc"

    def test_list_basic(self):
        assert self.res["arr"][0]["a"] == False  # noqa: E712

    def test_list_bool(self):
        assert self.res["arr"][1]["a"] == True  # noqa: E712

    def test_arr_expanded(self):
        assert self.res["arr"][1]["b"] == self.v

    def test_envvar_with_default_value_present(self):
        assert self.res["default_envvar_present"] == self.v

    def test_envvar_with_default_value_missing(self):
        assert self.res["default_envvar_missing"] == "bar"

    def test_envvar_with_default_int_value_present(self):
        assert self.res["default_int_present"] == 314

    def test_envvar_with_default_int_value_missing(self):
        assert self.res["default_int_missing"] == 42
