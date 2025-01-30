"""TODO: docstring"""

from druncschema.request_response_pb2 import Request, Response, Description
from druncschema.generic_pb2 import PlainText, PlainTextVector

from drunc.utils.shell_utils import GRPCDriver, DecodedResponse


class SessionManagerDriver(GRPCDriver):
    def __init__(self, address: str, token, **kwargs):
        super(SessionManagerDriver, self).__init__(
            name = 'session_manager_driver',
            address = address,
            token = token,
            **kwargs
        )

    def create_stub(self, channel):
        from druncschema.session_manager_pb2_grpc import SessionManagerStub
        return SessionManagerStub(channel)

    def describe(self) -> DecodedResponse:
        return self.send_command('describe', outformat = Description)
