.. _api-utils:

=========
Utils API
=========

The ``utils`` package contains utility classes and methods that are used throughout Brownie.

``brownie.utils.color``
=======================

The ``color`` module contains the ``Color`` class, used for to apply color and formatting to text before printing.

Color
-----

.. py:class:: brownie.utils.color.Color

    The ``Color`` class is used to apply color and formatting to text before displaying it to the user. It is primarily used within the console. An instance of ``Color`` is available at ``brownie.utils.color``:

    .. code-block:: python

        >>> from brownie.utils import color
        >>> color
        <brownie.utils.color.Color object at 0x7fa9ec851ba8>

    ``Color`` is designed for use in `formatted string literals <https://docs.python.org/3.6/reference/lexical_analysis.html#f-strings>`_. When called it returns an `ANSI escape code <https://en.wikipedia.org/wiki/ANSI_escape_code#Colors>`_ for the given color:

    .. code-block:: python

        >>> color('red')
        '\x1b[0;31m'

    You can also prefix any color with "bright" or "dark":

    .. code-block:: python

        >>> color('bright red')
        '\x1b[0;1;31m'
        >>> color('dark red')
        '\x1b[0;2;31m'

    Calling it with no values or Converting to a string returns the base color code:

    .. code-block:: python

        >>> color()
        '\x1b[0;m'
        >>> str(color)
        '\x1b[0;m'

Color Methods
*************

.. py:classmethod:: Color.pretty_dict(value, _indent=0) -> str

    Given a ``dict``, returns a colored and formatted string suitable for printing.

    * ``value``: ``dict`` to format
    * ``_indent``: used for recursive internal calls, should always be left as ``0``

.. py:classmethod:: Color.pretty_sequence(value, _indent=0) -> str

    Given a sequence (``list``, ``tuple``, ``set``), returns a colored and formatted string suitable for printing.

    * ``value``: Sequence to format
    * ``_indent``: used for recursive internal calls, should always be left as ``0``

.. py:classmethod:: Color.format_tb(exc, filename=None, start=None, stop=None) -> str

    Given a raised ``Exception``, returns a colored and formatted string suitable for printing.

    * ``exc``: An ``Exception`` object
    * ``filename``: An optional path as a string. If given, only lines in the traceback related to this filename will be displayed.
    * ``start``: Optional. If given, the displayed traceback not include items prior to this index.
    * ``stop``: Optional. If given, the displayed traceback not include items beyond this index.

.. py:classmethod:: Color.format_syntaxerror(exc) -> str

    Given a raised ``SyntaxError``, returns a colored and formatted string suitable for printing.

    * ``exc``: A ``SyntaxError`` object.
