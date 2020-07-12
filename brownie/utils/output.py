from collections import OrderedDict
from typing import Optional, Sequence, Union

from brownie.utils.color import Color

color = Color()


def build_tree(
    tree_dict: Union[OrderedDict, Sequence],
    multiline_pad: int = 1,
    _indent_data: Optional[list] = None,
) -> str:
    """
    Build a tree graph from a nested OrderedDict.

    Each dictionary key is a value to be added to the tree. The value may be:

    * an OrderedDict, containing keys to be placed beneath it within the tree
    * a List, for keys beneath it in the node when none also have their own sub-nodes
    * None, when the key has no subnode

    For keys that contain a new line, all lines beyond the first are indented. It
    is possible to create complex trees that contain subtrees, by using the tree_str
    of `build_tree` as a key value in another tree.

    Arguments
    ---------
    tree_dict : OrderedDict
        OrderedDict to be turned into a tree.
    multiline_pad : int, optional
        Number of padding lines to leave befor and after a tree value that spans
        multiple lines.
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

    was_padded = False
    for i, key in enumerate(tree_dict):
        is_last_item = bool(i < len(tree_dict) - 1)

        # create indentation string
        indent = f"{color('dark white')}"
        for value in _indent_data[1:]:
            indent = f"{indent}\u2502   " if value else f"{indent}    "
        if _indent_data:
            symbol = "\u251c" if is_last_item else "\u2514"
            indent = f"{indent}{symbol}\u2500\u2500 "

        lines = [i for i in key.split("\n") if i]
        if len(lines) > 1 and not was_padded:
            for i in range(multiline_pad):
                tree_str = f"{tree_str}{indent[:-4]}\u2502   \n"

        tree_str = f"{tree_str}{indent}{color}{lines[0]}\n"
        was_padded = False

        if len(lines) > 1:
            # handle multiline keys
            symbol = "\u2502" if is_last_item else " "
            symbol2 = "\u2502" if (isinstance(tree_dict, dict) and tree_dict[key]) else " "
            indent = f"{indent[:-4]}{symbol}   {symbol2}   "
            for line in lines[1:] + ([""] * multiline_pad):
                tree_str = f"{tree_str}{color('dark white')}{indent}{color}{line}\n"
            was_padded = True

        if isinstance(tree_dict, dict) and tree_dict[key]:
            # create nested tree
            nested_tree = build_tree(tree_dict[key], multiline_pad, _indent_data + [is_last_item])
            tree_str = f"{tree_str}{nested_tree}"

    return tree_str
