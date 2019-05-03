.. _api-utils:

=========
Utils API
=========


.. _api_alert:

Alerts and Callbacks
====================

The ``alert`` module is used to set up notifications and callbacks based on state changes in the blockchain.

.. py:attribute:: brownie.utils.alert

Alert
-----

Alerts and callbacks are handled by creating instances of the ``Alert`` class.

.. py:class:: brownie.utils.alert.Alert(fn, args=[], kwargs={}, delay=0.5, msg=None, callback=None)

    An alert object. It is active immediately upon creation of the instance.

    * ``fn``: A callable to check for the state change.
    * ``args``: Arguments to supply to the callable.
    * ``kwargs``: Keyword arguments to supply to the callable.
    * ``delay``: Number of seconds to wait between checking for changes.
    * ``msg``: String to display upon change. The string will have ``.format(initial_value, new_value)`` applied before displaying.
    * ``callback``: A callback function to call upon a change in value. It should accept two arguments, the initial value and the new value.

    A basic example of an alert, watching for a changed balance:

    .. code-block:: python

        >>> alert.Alert(accounts[1].balance, msg="Account 1 balance has changed from {} to {}")
        <lib.components.alert.Alert object at 0x7f9fd25d55f8>
        >>> alert.show()
        [<lib.components.alert.Alert object at 0x7f9fd25d55f8>]
        >>> accounts[2].transfer(accounts[1], "1 ether")

        Transaction sent: 0x912d6ac704e7aaac01be159a4a36bbea0dc0646edb205af95b6a7d20945a2fd2
        Transaction confirmed - block: 1   gas spent: 21000
        <Transaction object '0x912d6ac704e7aaac01be159a4a36bbea0dc0646edb205af95b6a7d20945a2fd2'>
        ALERT: Account 1 balance has changed from 100000000000000000000 to 101000000000000000000

    This example uses the alert's callback function to perform a token transfer, and sets a second alert to watch for the transfer:

    .. code-block:: python

        >>> alert.new(accounts[3].balance, msg="Account 3 balance has changed from {} to {}")
        <lib.components.alert.Alert object at 0x7fc743e415f8>
        >>> def on_receive(old_value, new_value):
        ...     accounts[2].transfer(accounts[3], new_value-old_value)
        ...
        >>> alert.new(accounts[2].balance, callback=on_receive)
        <lib.components.alert.Alert object at 0x7fc743e55cf8>
        >>> accounts[1].transfer(accounts[2],"1 ether")

        Transaction sent: 0xbd1bade3862f181359f32dac02ffd1d145fdfefc99103ca0e3d28ffc7071a9eb
        Transaction confirmed - block: 1   gas spent: 21000
        <Transaction object '0xbd1bade3862f181359f32dac02ffd1d145fdfefc99103ca0e3d28ffc7071a9eb'>

        Transaction sent: 0x8fcd15e38eed0a5c9d3d807d593b0ea508ba5abc892428eb2e0bb0b8f7dc3083
        Transaction confirmed - block: 2   gas spent: 21000
        ALERT: Account 3 balance has changed from 100000000000000000000 to 101000000000000000000

.. py:classmethod:: Alert.stop()

    Stops the alert.

    .. code-block:: python

        >>> alert_list = alert.show()
        [<lib.components.alert.Alert object at 0x7f9fd25d55f8>]
        >>> alert_list[0].stop()
        >>> alert.show()
        []

Module Methods
--------------

.. py:method:: new(fn, args=[], kwargs={}, delay=0.5, msg=None, callback=None)

    Alias for creating a new ``Alert`` instance.

    .. code-block:: python

        >>> alert.new(accounts[3].balance, msg="Account 3 balance has changed from {} to {}")
        <lib.components.alert.Alert object at 0x7fc743e415f8>

.. py:method:: show()

    Returns a list of all currently active alerts.

    .. code-block:: python

        >>> alert.new(accounts[1].balance, msg="Account 1 balance has changed from {} to {}")
        <lib.components.alert.Alert object at 0x7f9fd25d55f8>
        >>> alert.show()
        [<lib.components.alert.Alert object at 0x7f9fd25d55f8>]

.. py:method:: stop_all()

    Stops all currently active alerts.

    .. code-block:: python

        >>> alert.show()
        [<lib.components.alert.Alert object at 0x7f9fd25d55f8>]
        >>> alert.stop_all()
        >>> alert.show()
        []

Compiler
========

.. py:method:: compile_source(source)

    Compiles the given string and returns a list of ContractContainer instances.

    .. code-block:: python

        >>> container = compile_source('''pragma solidity 0.4.25;

        contract SimpleTest {

          string public name;

          constructor (string _name) public {
            name = _name;
          }
        }'''

        [<ContractContainer object 'SimpleTest'>]
        >>> container[0]
        []

Sha_Compare
===========
