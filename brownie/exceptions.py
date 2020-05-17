#!/usr/bin/python3

import json
import sys
from typing import Any, Type

import psutil

# network


class UnknownAccount(Exception):
    pass


class UndeployedLibrary(Exception):
    pass


class UnsetENSName(Exception):
    pass


class IncompatibleEVMVersion(Exception):
    pass


class RPCProcessError(Exception):
    def __init__(self, cmd: str, uri: str) -> None:
        super().__init__(f"Unable to launch local RPC client.\nCommand: {cmd}\nURI: {uri}")


class RPCConnectionError(Exception):
    def __init__(self, cmd: str, proc: psutil.Popen, uri: str) -> None:
        msg = (
            "Able to launch RPC client, but unable to connect."
            f"\n\nCommand: {cmd}\nURI: {uri}\nExit Code: {proc.poll()}"
        )
        if sys.platform != "win32":
            out = proc.stdout.read().decode().strip() or "  (Empty)"
            err = proc.stderr.read().decode().strip() or "  (Empty)"
            msg = f"{msg}\n\nStdout:\n{out}\n\nStderr:\n{err}"
        super().__init__(msg)


class RPCRequestError(Exception):
    pass


class MainnetUndefined(Exception):
    pass


class VirtualMachineError(Exception):

    """Raised when a call to a contract causes an EVM exception.

    Attributes:
        revert_msg: The returned error string, if any.
        source: The contract source code where the revert occured, if available."""

    def __init__(self, exc: Any) -> None:
        if type(exc) is not dict:
            try:
                exc = eval(str(exc))
            except SyntaxError:
                exc = {"message": str(exc)}
        self.revert_msg = msg = exc["message"]
        self.source = exc.get("source", "")
        if self.source:
            msg = f"{msg}\n{self.source}"
        super().__init__(msg)


class EventLookupError(LookupError):
    pass


class NamespaceCollision(AttributeError):
    pass


# project/


class ContractExists(Exception):
    pass


class ContractNotFound(Exception):
    pass


class ProjectAlreadyLoaded(Exception):
    pass


class ProjectNotFound(Exception):
    pass


class CompilerError(Exception):
    def __init__(self, e: Type[psutil.Popen]) -> None:
        err = [i["formattedMessage"] for i in json.loads(e.stdout_data)["errors"]]
        super().__init__("Compiler returned the following errors:\n\n" + "\n".join(err))


class IncompatibleSolcVersion(Exception):
    pass


class PragmaError(Exception):
    pass


class InvalidManifest(Exception):
    pass


class UnsupportedLanguage(Exception):
    pass


class InvalidPackage(Exception):
    pass


class BrownieCompilerWarning(Warning):
    pass


class BrownieEnvironmentWarning(Warning):
    pass


class InvalidArgumentWarning(BrownieEnvironmentWarning):
    pass


class BrownieTestWarning(Warning):
    pass
