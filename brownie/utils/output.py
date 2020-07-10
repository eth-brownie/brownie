from collections import OrderedDict
from typing import Optional

from brownie.utils.color import Color

color = Color()


def build_tree(
    tree_dict: OrderedDict, multiline_pad: int = 1, _indent_data: Optional[list] = None,
) -> str:
    """
    Build a tree graph from a nested OrderedDict.

    Each dictionary key is a value to be added to the tree. It's value must also
    be an OrderedDict, containing keys to be placed beneath it within the tree.

    For keys that contain a new line, all lines beyond the first are indented. It
    is possible to create complex trees that contain subtrees, by using the tree_str
    of `build_tree` as a key value in another tree.

    Arguments
    ---------
    tree_dict : OrderedDict
        OrderedDict to be turned into a tree.
    multiline_pad : int, optional
        Number of empty lines to leave after a tree value spanning multiple lines.
    _indent_data
        Internal list to handle indentation during recursive calls. The initial
        call to this function should always leave this value as `None`.

    Returns
    -------
    str
        Tree graph.
    """
    tree_str = f"{color('dark white')}"
    if _indent_data is None:
        _indent_data = []

    for i, key in enumerate(tree_dict):
        is_last_item = bool(i < len(tree_dict) - 1)

        # create indentation string
        indent = f"{color('dark white')}"
        for value in _indent_data[1:]:
            indent = f"{indent}\u2502   " if value else f"{indent}    "
        if _indent_data:
            symbol = "\u251c" if is_last_item else "\u2514"
            indent = f"{indent}{symbol}\u2500\u2500 "

        lines = key.split("\n")
        tree_str = f"{tree_str}{indent}{color}{lines[0]}\n"

        if len(lines) > 1:
            # handle multiline keys
            symbol = "\u2502" if is_last_item else " "
            symbol2 = "\u2502" if tree_dict[key] else " "
            indent = f"{indent[:-4]}{symbol}   {symbol2}   "
            for line in lines[1:] + ([""] * multiline_pad):
                tree_str = f"{tree_str}{color('dark white')}{indent}{color}{line}\n"

        if tree_dict[key]:
            # create nested tree
            nested_tree = build_tree(tree_dict[key], multiline_pad, _indent_data + [is_last_item])
            tree_str = f"{tree_str}{nested_tree}"

    return tree_str
