from typing import List, Optional, Sequence


def build_tree(
    tree_structure: Sequence,
    multiline_pad: int = 1,
    pad_depth: Optional[List[int]] = None,
    _indent_data: Optional[list] = None,
) -> str:
    """
    Build a tree graph from a nested list.

    Each item in the list if a top-level value to be added to the tree. The item may be:


    * A sequence, where the first value is the key and each subsequent value is
      a node beneath it.
    * A string, where the value is a key with no subnodes

    By nesting sequences it is possible to produce multi-level trees.

    For keys that contain a new line, all lines beyond the first are indented. It
    is possible to create complex trees that contain subtrees, by using the tree_str
    of `build_tree` as a key value in another tree.

    Arguments
    ---------
    tree_structure : Sequence
        List or tuple to be turned into a tree.
    multiline_pad : int, optional
        Number of padding lines to leave before and after a tree value that spans
        multiple lines.
    pad_depth : List[int], optional
        Number of padding lines to leave between each node. Each entry in the list
        represents padding at a specific depth of the tree. If no value is given,
        zero is assumed.
    _indent_data
        Internal list to handle indentation during recursive calls. The initial
        call to this function should always leave this value as `None`.

    Returns
    -------
    str
        Tree graph.
    """
    tree_str = ""
    if _indent_data is None:
        _indent_data = []

    was_padded = False
    for i, row in enumerate(tree_structure):
        is_last_item = bool(i < len(tree_structure) - 1)

        # create indentation string
        indent = ""
        for value in _indent_data[1:]:
            indent = f"{indent}\u2502   " if value else f"{indent}    "
        if _indent_data:
            symbol = "\u251c" if is_last_item else "\u2514"
            indent = f"{indent}{symbol}\u2500\u2500 "

        key = row[0] if isinstance(row, (list, tuple)) else row
        lines = [x for x in key.split("\n") if x]
        if pad_depth and i > 0:
            for x in range(pad_depth[0]):
                tree_str = f"{tree_str}{indent[:-4]}\u2502   \n"
        elif len(lines) > 1 and not was_padded:
            for x in range(multiline_pad):
                tree_str = f"{tree_str}{indent[:-4]}\u2502   \n"

        tree_str = f"{tree_str}{indent}{lines[0]}\n"
        was_padded = False

        if len(lines) > 1:
            # handle multiline keys
            symbol = "\u2502" if is_last_item else " "
            symbol2 = "\u2502" if isinstance(row, (list, tuple)) and len(row) > 1 else " "
            indent = f"{indent[:-4]}{symbol}   {symbol2}   "
            for line in lines[1:] + ([""] * multiline_pad):
                tree_str = f"{tree_str}{indent}{line}\n"
            was_padded = True

        if isinstance(row, (list, tuple)) and len(row) > 1:
            # create nested tree
            new_pad_depth = pad_depth[1:] if pad_depth else None
            nested_tree = build_tree(
                row[1:], multiline_pad, new_pad_depth, _indent_data + [is_last_item]
            )
            tree_str = f"{tree_str}{nested_tree}"

    return tree_str
