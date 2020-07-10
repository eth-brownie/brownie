from collections import OrderedDict
from typing import Optional

from brownie.utils import color


def build_tree(
    tree_dict: OrderedDict, empty_lines: int = 1, _indent_data: Optional[list] = None
) -> str:
    result = f"{color('dark white')}"
    if _indent_data is None:
        _indent_data = []

    for i, key in enumerate(tree_dict):
        is_last_item = i < len(tree_dict) - 1

        indent = ""
        for value in _indent_data[1:]:
            indent = f"{indent}\u2502 " if value else f"{indent}  "
        if _indent_data:
            indent = f"{indent}\u251c\u2500" if is_last_item else f"{indent}\u2514\u2500"

        if "\n" in key:
            lines = key.split("\n")
            result = f"{result}{indent}{lines[0]}\n"
            symbol = "\u2502" if is_last_item else " "
            symbol2 = "\u2502" if tree_dict[key] else " "
            indent = f"{indent[:-2]}{symbol} {symbol2}   "
            for line in lines[1:] + ([""] * empty_lines):
                result = f"{result}{color('dark white')}{indent}{color}{line}\n"
        else:
            result = f"{result}{indent}{color}{key}\n"

        inner_tree = build_tree(tree_dict[key], empty_lines, _indent_data + [is_last_item])
        result = f"{result}{inner_tree}"

    return result
