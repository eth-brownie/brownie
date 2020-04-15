.. _config:

======================
The Configuration File
======================

Brownie projects may optionally include a configuration file to modify certain behaviors.

The configuration file must be saved as ``brownie-config.yaml`` in the root folder or your project. All fields are optional. You can copy from the examples below and modify the settings as required.

Default Configuration
=====================

The following example shows all configuration settings and their default values:

.. literalinclude:: ../brownie/data/default-config.yaml
    :linenos:
    :lines: 8-
    :language: yaml

Settings
========

Networks
--------

.. _config-network:

.. py:attribute:: default

    The default network that Brownie connects. If a different network is required, you can override this setting with the ``--network`` flag in the command line.

    default value: ``development``

.. py:attribute:: networks.development

.. py:attribute:: networks.live

    Default settings for development and live environments.

    .. py:attribute:: gas_price

        The default gas price for all transactions. If set to ``auto`` the gas price is determined using ``web3.eth.gasPrice``.

        development default: ``0``

        live default: ``auto``

    .. py:attribute:: gas_limit

        The default gas limit for all transactions. If set to ``auto`` the gas limit is determined using ``web3.eth.estimateGas``.

        development default: ``6721975``

        live default: ``auto``

    .. py:attribute:: default_contract_owner

        If ``false``, deployed contracts will not remember the account that they were created by. Every transaction will require a ``from`` kwarg.

    .. py:attribute:: reverting_tx_gas_limit

        The gas limit to use when a transaction would revert. If set to ``false``, transactions that would revert will instead raise a :func:`VirtualMachineError <brownie.exceptions.VirtualMachineError>`.

        development default: ``6721975``

        live default: ``false``

.. _config-solc:


Compiler
--------

Compiler settings. See :ref:`compiler settings<compile_settings>` for more information.

.. py:attribute:: evm_version

    The EVM version to compile for. If ``null`` the most recent one is used. Possible values are ``byzantium``, ``constantinople``, ``petersburg``, ``istanbul``, ``atlantis`` and ``agharta``.

    default value: ``null``

.. py:attribute:: compiler.solc

    Settings specific to the Solidity compiler.

    .. py:attribute:: version

        The version of solc to use. Should be given as a string in the format ``0.x.x``. If set to ``null``, the version is set based on the contract pragma. Brownie supports solc versions ``>=0.4.22``.

        default value: ``null``

    .. py:attribute:: optimizer

        Optimizer settings to be passed to the Solidity compiler. Values given here are passed into the compiler with no reformatting. See the `Solidity documentation <https://solidity.readthedocs.io/en/latest/using-the-compiler.html#input-description>`_ for a list of possible values.

    .. py:attribute:: remappings

        Optional field used to supply :ref:`path remappings <compile-remap>`.

        .. code-block:: yaml

            remappings:
              - zeppelin=/usr/local/lib/open-zeppelin/contracts/
              - github.com/ethereum/dapp-bin/=/usr/local/lib/dapp-bin/

.. _config-hypothesis:

Hypothesis
----------

Default settings for :ref:`property-based<hypothesis>` and :ref:`stateful<hypothesis-stateful>` test execution. See the Hypothesis `settings documentation <https://hypothesis.readthedocs.io/en/latest/settings.html#available-settings>`_ for a complete list of available settings.

.. code-block:: yaml

    hypothesis:
        deadline: null
        max_examples: 50
        stateful_step_count: 10

Other Settings
--------------

.. py:attribute:: autofetch_sources

    If enabled, Brownie will always attempt to fetch source code for unknown addresses using :func:`Contract.from_explorer <Contract.from_explorer>`.

    default value: ``false``

.. py:attribute:: show_colors

    Enable or disable colorful console output.

    default value: ``true``

.. py:attribute:: dependencies

    A list of packages that a project depends on. Brownie will attempt to install all listed dependencies prior to compiling the project.

    .. code-block:: yaml

        dependencies:
            - aragon/aragonOS@4.0.0
            - defi.snakecharmers.eth/compound@1.1.0

    See the :ref:`Brownie Package Manager<package-manager>` to learn more about package dependencies.
