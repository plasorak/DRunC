from google.rpc import code_pb2

from drunc.exceptions import DruncCommandException

from druncschema.authoriser_pb2 import ActionType


class Unauthorised(DruncCommandException):
    def __init__(self, user, action, command, drunc_system):
        self.user = user
        self.action = action
        self.action_name = ActionType.Name(action)
        self.command = command
        self.drunc_system = drunc_system

        super(Unauthorised, self).__init__(
            txt = f"\'{user}\' is not authorised to \'{self.action_name}\', required for command \'{command}\' on \'{drunc_system}\'",
            code = code_pb2.PERMISSION_DENIED,
        )
