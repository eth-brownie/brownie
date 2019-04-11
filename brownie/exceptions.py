#!/usr/bin/python3

import json


class CompilerError(Exception):

    def __init__(self, e):
        err = [i['formattedMessage'] for i in json.loads(e.stdout_data)['errors']]
        super().__init__("Compiler returned the following errors:\n\n"+"\n".join(err))


class VirtualMachineError(Exception):

    '''Raised when a call to a contract causes an EVM exception.

    Attributes:
        revert_msg: The returned error string, if any.
        source: The contract source code where the revert occured, if available.'''

    revert_msg = ""
    source = ""

    def __init__(self, exc):
        if type(exc) is not dict:
            try:
                exc = eval(str(exc))
            except SyntaxError:
                exc = {'message': str(exc)}
        if len(exc['message'].split('revert ', maxsplit=1)) > 1:
            self.revert_msg = exc['message'].split('revert ')[-1]
        if 'source' in exc:
            self.source = exc['source']
            super().__init__(exc['message']+"\n"+exc['source'])
        else:
            super().__init__(exc['message'])

