
.. _gui:

.. raw:: html

    <style>
    .green {background:#228822; color: #ffffff; padding: 2px 5px;}
    .yellow {background:#ff9933; color: #ffffff; padding: 2px 5px;}
    .orange {background:#ff3300; color: #ffffff; padding: 2px 5px;}
    .red {background:#882222; color: #ffffff; padding: 2px 5px;}
    </style>

.. role:: green
.. role:: yellow
.. role:: orange
.. role:: red

===============
The Brownie GUI
===============

Brownie includes a GUI for viewing test coverage data and analyzing the compiled bytecode of your contracts.

Parts of this section assume a level of familiarity with EVM bytecode. If you are looking to learn more about the subject, Alejandro Santander from `OpenZeppelin <https://openzeppelin.com/>`_ has written an excellent guide - `Deconstructing a Solidity Contract <https://blog.openzeppelin.com/deconstructing-a-solidity-contract-part-i-introduction-832efd2d7737/>`_.

.. note::

    If you receive an error when attempting to load the GUI, you probably do not have Tk installed on your system. See the :ref:`Tk installation instrucions<install-tk>` for more detailed information.

Getting Started
===============

To open the GUI, run the following command from within your project folder:

::

    $ brownie gui

Or from the console:

.. code-block:: python

    >>> Gui()

Once loaded, the first thing you'll want to do is choose a contract to view. To do this, click on the drop-down list in the upper right that says "Select a Contract". You will see a list of every deployable contract within your project.

Once selected, the contract source code is displayed in the main window with a list of opcodes and program counters on the right. If the contract inherits from more than one source file, tabs will be available to switch between sources. For example, in the image below the ``Token`` contract includes both ``Token.sol`` and ``SafeMath.sol``:

.. image:: gui1.png
   :alt: The Brownie GUI

Working with Opcodes
====================

Mapping Opcodes to Source
-------------------------

Highlighting a section of code will also highlight the instructions that are associated with it. Similarly, selecting on an instruction will highlight the related source.

Click the ``Scope`` button in the top left (or the ``S`` key) to filter the list of instructions such that only those contained within the highlighted source are shown.

.. note::

    Opcodes displayed with a dark background are not mapped to any source, or are mapped to the source of the entire contract. These are typically the result of compiler optimization or part of the initial function selector.

.. image:: gui2.png
   :alt: Mapping Opcodes to Source

Jump Instructions
-----------------

Click the ``Console`` button in the top left (or the ``C`` key) to expand the console. It shows more detailed information about the highlighted instruction.

* When you select a ``JUMP`` or ``JUMPI`` instruction, the console includes a "Target:" field that gives the program counter for the related ``JUMPDEST``, where possible. The related ``JUMPDEST`` is also highlighted in green. Press the ``J`` key to show the instruction.
* When you select a ``JUMPDEST`` instruction, the console includes a "Jumps:" field that gives a list of program counters that point at the highlighted instruction.  Each related ``JUMP``/``JUMPI`` is also highlighted in green.

.. image:: gui3.png
   :alt: Jump Instructions

Miscellaneous
-------------

* Right clicking on an instruction will apply a yellow highlight to all instructions of the same opcode type.
* Press the ``R`` key to toggle highlight on all ``REVERT`` opcodes.

.. _coverage-gui:

Viewing Coverage Data
=====================

For an in-depth look at your test coverage, click on the drop-down list in the upper right that says "Select Report" and choose "coverage". A new drop-down list will appear where you can select which type of coverage data to view (branches or statements).

Relevant code will be highlighted in different colors:

* :green:`Green` code was executed during the tests
* :yellow:`Yellow` branch code executed, but only evaluated truthfully
* :orange:`Orange` branch code executed, but only evaluated falsely
* :red:`Red` code did not execute during the tests

.. image:: gui4.png
   :alt: Viewing Coverage Data

.. _gui-report-json:


Viewing Security Report Data
============================

Once the :code:`brownie analyze` command has finished, the GUI will show a new security report.
Select the :code:`security` report and the :code:`MythX` report type.
If any vulnerabilities have been found, they will be highlighted based on their severity:

* :green:`Green` Low severity (best practice violations)
* :yellow:`Yellow` Medium severity (potential vulnerability), needs to be fixed
* :red:`Red` High severity (critical, immediate danger of exploitation)

The report data can also be directly accessed in :code:`reports/security.json`.

.. image:: gui5.png
   :alt: Security Report GUI


Report JSON Format
==================

Project coverage data is saved to ``reports/coverage.json`` using Brownie's standard report format. Third party tools wishing to display information in the Brownie GUI can also save JSON files within the ``reports/`` folder.

Brownie expects JSON reports to use the following structure:

.. code-block:: javascript

    {
        "highlights": {
            // this name is shown in the report type drop-down menu
            "<Report Type>": {
                "ContractName": {
                    "path/to/sourceFile.sol": [
                        // start offset, stop offset, color, optional message
                        [123, 440, "green", ""],
                        [502, 510, "red", ""],
                    ]
                }
            }
        },
        "sha1": {} // optional, not yet implemented
    }

The final item in each highlight offset is an optional message to be displayed. If included, the text given here will be shown in the GUI console when the user hovers the mouse over the highlight. To not show a message, set it to ``""`` or ``null``.
