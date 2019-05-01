.. _api-types:

=========
Types API
=========



Convert
=======

.. _wei:

.. py:method:: wei(value)

    Converts a value to wei. Useful for strings where you specify the unit, or for large floats given in scientific notation, where a direct conversion to ``int`` would cause inaccuracy from floating point errors.

    ``wei`` is automatically applied in all Brownie methods when an input is meant to specify an amount of ether.

    .. code-block:: python

        >>> wei("1 ether")
        1000000000000000000
        >>> wei("12.49 gwei")
        12490000000
        >>> wei("0.029 shannon")
        29000000
        >>> wei(8.38e32)
        838000000000000000000000000000000


Types
=====
