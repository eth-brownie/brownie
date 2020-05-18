#!/usr/bin/python3

import sys
from typing import Optional, Type

import psutil
import yaml

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

    """
    Raised when a call to a contract causes an EVM exception.

    Attributes
    ----------
    message : str
        The full error message received from the RPC client.
    revert_msg : str
        The returned error string, if any.
    revert_type : str
        The error type.
    pc : int
        The program counter where the error was raised.
    txid : str
        The transaction ID that raised the error.
    """

    def __init__(self, exc: ValueError) -> None:
        try:
            exc = yaml.safe_load(str(exc))
        except Exception:
            pass

        if isinstance(exc, dict) and "message" in exc:
            self.message: str = exc["message"]
            try:
                txid, data = next((k, v) for k, v in exc["data"].items() if k.startswith("0x"))
            except StopIteration:
                return

            self.txid: str = txid
            self.revert_type: str = data["error"]
            self.revert_msg: Optional[str] = data.get("reason")
            self.pc: Optional[str] = data.get("program_counter")
            if self.revert_type == "revert":
                self.pc -= 1
        else:
            self.message = str(exc)

    def __str__(self) -> str:
        if not hasattr(self, "revert_type"):
            return self.message
        msg = self.revert_type
        if self.revert_msg:
            msg = f"{msg}: {self.revert_msg}"
        if hasattr(self, "source"):
            msg = f"{msg}\n{self.source}"
        return msg

    def _with_source(self, source: str) -> "VirtualMachineError":
        self.source = source
        return self


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
        err = [i["formattedMessage"] for i in yaml.safe_load(e.stdout_data)["errors"]]
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
