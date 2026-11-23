.. _config:

======================
The Configuration File
======================

You can modify Brownie's default behaviours by creating an optional configuration file.

The configuration file must be saved as ``brownie-config.yaml``. If saved in the root directory of a project it will be loaded whenever that project is active. If saved in your `home path <https://docs.python.org/3/library/pathlib.html#pathlib.Path.home>`_, it will always be loaded.

All configuration fields are optional. You can copy from the examples below and modify the settings as required.

Configuration values can also be set using environment variables, as well as by specifying the `dotenv` top-level key.

Default Configuration
=====================

The following example shows all configuration settings and their default values:

.. literalinclude:: ../brownie/data/default-config.yaml
    :linenos:
    :lines: 8-
    :language: yaml

Variable Expansion
==================

Brownie supports POSIX-style variable expansion for environment variables.

.. code-block:: yaml

    networks:
        default: ${DEFAULT_NETWORK}

You can also provide defaults.

.. code-block:: yaml

    networks:
        default: ${DEFAULT_NETWORK:-mainnet}

Settings
========

Project Structure
-----------------

.. _config-project-structure:

Project subdirectory names. Include these fields if you wish to modify the default structure of your project.

.. py:attribute:: project_structure.build

    Project subdirectory that stores data such as compiler artifacts and unit test results.

    default value: ``build``

.. py:attribute:: project_structure.contracts

    Project subdirectory that stores contract source files.

    default value: ``contracts``

.. py:attribute:: project_structure.interfaces

    Project subdirectory that stores interface source files and ABIs.

    default value: ``interfaces``

.. py:attribute:: project_structure.reports

    Project subdirectory that stores JSON report files.

    default value: ``reports``

.. py:attribute:: project_structure.scripts

    Project subdirectory that stores scripts for deployment and interaction.

    default value: ``scripts``

.. py:attribute:: project_structure.tests

    Project subdirectory that stores unit tests.

    default value: ``tests``

Networks
--------

.. _config-network:

.. py:attribute:: default

    The default network that Brownie connects. If a different network is required, you can override this setting with the ``--network`` flag in the command line.

    default value: ``development``

.. py:attribute:: networks.development

    This setting is only available for development networks.

    .. py:attribute:: cmd_settings

        Additional commandline parameters, which are passed into Ganache as commandline arguments. These settings will update the network specific settings defined in :ref:`network management<adding-network>` whenever the project with this configuration file is active.

        The following example shows all commandline settings with their default value. ``fork``, ``disable_cache`` and ``unlock`` have no default values. ``network_id`` and ``time`` will default to the current timestamp or time respectively. See :ref:`adding a development network<adding-network>` for more details on the arguments.

    .. code-block:: yaml

        networks:
            development:
                gas_limit: max
                gas_buffer: 1
                gas_price: 0
                max_fee: null
                priority_fee: null
                reverting_tx_gas_limit: max
                default_contract_owner: true
                cmd_settings:
                    port: 8545
                    gas_limit: 6721975
                    accounts: 10
                    chain_id: 1337
                    network_id: 1588949648
                    evm_version: istanbul
                    fork: null
                    disable_cache: null
                    mnemonic: brownie
                    block_time: 0
                    default_balance: 100
                    time: 2020-05-08T14:54:08+0000
                    unlock: null

.. py:attribute:: networks.live

    Default settings for development and live environments.

    .. py:attribute:: gas_limit

        The default gas limit for all transactions. If set to ``auto`` the gas limit is determined using ``web3.eth.estimate_gas``. If set to ``max``, the block gas limit is used.

        development default: ``max``

        live default: ``auto``

    .. py:attribute:: gas_buffer

        A modifier applied to ``web3.eth.estimate_gas`` when determining gas price automatically.

        development default: ``1``

        live default: ``1.1``

    .. py:attribute:: gas_price

        The default gas price for all transactions. If set to ``auto`` the gas price is determined using ``web3.eth.gas_price``.

        development default: ``0``

        live default: ``auto``

    .. py:attribute:: max_fee

        The default max fee per gas for all transactions. If set to ``null``, transactions will default to legacy-style (using ``gas_price``).

        default: ``null``

    .. py:attribute:: priority_fee

        The default max priority fee per gas for all transactions. If set to ``null``, transactions will default to legacy-style (using ``gas_price``).

        default: ``null``

    .. py:attribute:: default_contract_owner

        If ``false``, deployed contracts will not remember the account that they were created by. Every transaction will require a ``from`` kwarg.

    .. py:attribute:: reverting_tx_gas_limit

        The gas limit to use when a transaction would revert. If set to ``false``, transactions that would revert will instead raise a :func:`VirtualMachineError <brownie.exceptions.VirtualMachineError>`.

        development default: ``max``

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

    .. py:attribute:: viaIR

        Enable solc compilation pipeline to go through the Yul Intermediate Representation to generate IR-based EVM bytecode. See the `Solidity documentation <https://docs.soliditylang.org/en/latest/ir-breaking-changes.html>`_ for breaking changes.

        default value: ``false``

    .. py:attribute:: optimizer

        Optimizer settings to be passed to the Solidity compiler. Values given here are passed into the compiler with no reformatting. See the `Solidity documentation <https://solidity.readthedocs.io/en/latest/using-the-compiler.html#input-description>`_ for a list of possible values.

    .. py:attribute:: remappings

        Optional field used to supply :ref:`path remappings <compile-remap>`.

        .. code-block:: yaml

            remappings:
              - zeppelin=/usr/local/lib/open-zeppelin/contracts/
              - github.com/ethereum/dapp-bin/=/usr/local/lib/dapp-bin/

    .. py:attribute:: use_latest_patch

        Optional boolean or array contract list to use the latest patch semver compiler version. E.g. the if the contract has pragma version `0.4.16` and the latest available patch for `0.4` is `0.4.22` it will use this instead for compilations.

        Enable for all contracts:
        .. code-block:: yaml
            compiler:
                solc:
                    use_latest_patch: true

        Enable for only specific contracts:
        .. code-block:: yaml
            compiler:
                solc:
                    use_latest_patch:
                        - '0x514910771AF9Ca656af840dff83E8264EcF986CA'

.. py:attribute:: compiler.vyper

    Settings specific to the Vyper compiler.

    .. py:attribute:: version

        The version of vyper to use. Should be given as a string in the format ``0.x.x``. If set to ``null``, the version is set based on the contract pragma. Brownie supports vyper versions ``>=0.1.0-beta.16``.

        default value: ``null``

Console
-------

.. py:attribute:: show_colors

    Enable or disable colorful output.

    default value: ``true``

.. py:attribute:: color_style

    Set the Pygments `color style <https://pygments.org/docs/styles/#getting-a-list-of-available-styles>`_ used within the console and throughout Brownie.

    You can view a gallery of popular styles `here <https://help.farbox.com/pygments.html>`_.

    default value: ``monokai``

.. py:attribute:: auto_suggest

    Enable or disable type hints for contract function inputs.

    default value: ``true``

.. py:attribute:: completions

    Enable or disable autocompletion.

    default value: ``true``

.. py:attribute:: editing_mode

    Choose between ``emacs`` and ``vi`` console editing modes.

    default value: ``emacs``

.. _config-reports:

Reports
-------

Settings related to reports such as coverage data and gas profiles.

.. py:attribute:: exclude_paths

    Paths or `glob patterns <https://en.wikipedia.org/wiki/Glob_%28programming%29>`_ of source files to be excluded from report data.

    default value: ``null``

    .. code-block:: yaml

        reports:
            exclude_paths:
                - contracts/mocks/**/*.*
                - contracts/SafeMath.sol

.. py:attribute:: exclude_contracts

    Contract names to be excluded from report data.

    default value: ``null``

    .. code-block:: yaml

        reports:
            exclude_contracts:
                - SafeMath
                - Owned

.. py:attribute:: only_include_project

    If ``false``, reports also include contracts imported from outside the active project (such as those compiled via :func:`compile_source <main.compile_source>`).

    default value: ``true``

.. _config-hypothesis:

Hypothesis
----------

Default settings for :ref:`property-based<hypothesis>` and :ref:`stateful<hypothesis-stateful>` test execution. See the Hypothesis `settings documentation <https://hypothesis.readthedocs.io/en/latest/settings.html#available-settings>`_ for a complete list of available settings.

.. code-block:: yaml

    hypothesis:
        deadline: null
        max_examples: 50
        report_multiple_bugs: False
        stateful_step_count: 10
        deadline: null
        phases:
            explicit: true
            reuse: true
            generate: true
            target: true
            shrink: true

Other Settings
--------------

.. py:attribute:: autofetch_sources

    If enabled, Brownie will always attempt to fetch source code for unknown addresses using :func:`Contract.from_explorer <Contract.from_explorer>`.

    default value: ``false``

.. py:attribute:: dependencies

    A list of packages that a project depends on. Brownie will attempt to install all listed dependencies prior to compiling the project.

    .. code-block:: yaml

        dependencies:
            - aragon/aragonOS@4.0.0
            - defi.snakecharmers.eth/compound@1.1.0

    See the :ref:`Brownie Package Manager<package-manager>` to learn more about package dependencies.

.. _dev_artifacts:

.. py:attribute:: dev_deployment_artifacts

    If enabled, Brownie will save deployment artifacts for contracts deployed on development networks and will include the "dev" network on the deployment map.

    This is useful if another application, such as a front end framework, needs access to deployment artifacts while you are on a development network.

    default value: ``false``

.. py:attribute:: dotenv

    If present, Brownie will load the .env file, resolving the file relative to the project root. Will fail loudly if .env file is missing.

    .. code-block:: yaml

        dotenv: .env

.. py:attribute:: eager_caching
    If set to ``false``, brownie will not start the background caching thread and will only call the RPC on an as-needed basis.

    This is useful for always-on services or while using pay-as-you-go private RPCs

    default value: ``true``
