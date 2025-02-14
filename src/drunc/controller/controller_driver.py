from druncschema.request_response_pb2 import Description
from druncschema.generic_pb2 import PlainText
from druncschema.controller_pb2 import Status

from drunc.utils.shell_utils import GRPCDriver, DecodedResponse


class ControllerDriver(GRPCDriver):
    def __init__(self, address:str, token, **kwargs):
        super(ControllerDriver, self).__init__(
            name = 'controller_driver',
            address = address,
            token = token,
            **kwargs
        )

    def create_stub(self, channel):
        from druncschema.controller_pb2_grpc import ControllerStub
        return ControllerStub(channel)

    def describe(self) -> DecodedResponse:
        return self.send_command('describe', outformat = Description)

    def describe_fsm(self, key:str=None) -> DecodedResponse: # key can be: a state name, a transition name, none to get the currently accessible transitions, or all-transition for all the transitions
        from druncschema.controller_pb2 import FSMCommandsDescription
        input = PlainText(text = key)
        return self.send_command('describe_fsm', data = input, outformat = FSMCommandsDescription)

    def status(self) -> DecodedResponse:
        return self.send_command('status', outformat = Status)

    def take_control(self) -> DecodedResponse:
        return self.send_command('take_control', outformat = PlainText)

    def who_is_in_charge(self, rethrow=None) -> DecodedResponse:
        return self.send_command('who_is_in_charge', outformat = PlainText)

    def surrender_control(self) -> DecodedResponse:
        return self.send_command('surrender_control')

    def execute_fsm_command(self, arguments) -> DecodedResponse:
        from druncschema.controller_pb2 import FSMCommandResponse
        return self.send_command('execute_fsm_command', data = arguments, outformat = FSMCommandResponse)

    def include(self, arguments) -> DecodedResponse:
        return self.send_command('include', data = arguments, outformat = PlainText)

    def exclude(self, arguments) -> DecodedResponse:
        return self.send_command('exclude', data = arguments, outformat = PlainText)





