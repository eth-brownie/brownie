.. _static-analysis:

==========================
Static Analysis with MythX
==========================

TODO

To prevent vulnerabilities from being introduced to the code base, Brownie a
includes plugin that integrates automated security scans using the
`MythX <https://mythx.io/>`_ analysis API.
Simply run :code:`brownie analyze` on your compiled project directory.
This will send the compiled build artifacts to MythX for analysis. By default
no login is required and the analysis is going to be executed as a trial user.
To access more vulnerability information, register for free on the MythX
website and pass your login data via environment variables or command line
arguments.

::

    Brownie v1.0.0 - Python development framework for Ethereum

    Usage: brownie analyze [options] [--async | --interval=<sec>]

    Options:
    --gui                     Launch the Brownie GUI after analysis
    --full                    Perform a full scan (MythX Pro required)
    --interval=<sec>          Result polling interval in seconds [default: 3]
    --async                   Do not poll for results, print job IDs and exit
    --access-token=<string>   The JWT access token from the MythX dashboard
    --eth-address=<string>    The address of your MythX account
    --password=<string>       The password of your MythX account
    --help -h                 Display this message

    Use the "analyze" command to submit your project to the MythX API for
    smart contract security analysis.

    To authenticate with the MythX API, it is recommended that you provide
    the MythX JWT access token. It can be obtained on the MythX dashboard
    site in the profile section. They should be passed through the environment
    variable "MYTHX_ACCESS_TOKEN". If that is not possible, it can also be
    passed explicitly with the respective command line option.

    Alternatively, you have to provide a username/password combination. It
    is recommended to pass them through the environment variables as
    "MYTHX_ETH_ADDRESS" and "MYTHX_PASSWORD".

    You can also choose to not authenticate and submit your analyses as a free
    trial user. No registration required! To see your past analyses, get access
    to deeper vulnerability detection, and a neat dashboard, register at
    https://mythx.io/. Any questions? Hit up dominik.muhs@consensys.net or contact
    us on the website!

Once the analysis is done, the vulnerabilities are stored in the
:code:`reports/` directory. With :code:`brownie analyze --gui` the GUI can be
started automatically once the analysis has finished.

.. image:: gui5.png
   :alt: Security Report GUI
