from drunc.controller.children_interface.child_node import ChildNode
from drunc.utils.utils import ControlType
from drunc.controller.utils import send_command
from drunc.utils.grpc_utils import pack_to_any
from drunc.fsm.configuration import FSMConfHandler
from drunc.fsm.core import FSM
from druncschema.controller_pb2 import Status
from druncschema.request_response_pb2 import Response, ResponseFlag
from druncschema.controller_pb2 import FSMCommandResponse, FSMResponseFlag
from druncschema.generic_pb2 import PlainText, Stacktrace
from druncschema.token_pb2 import Token



class ClientSideState:

    def __init__(self, initial_state='initial'):
        # We'll wrap all these in a mutex for good measure
        from threading import Lock
        self._state_lock = Lock()
        self._executing_command = False
        self._assumed_operational_state = initial_state
        self._included = True
        self._errored = False


    def executing_command_mark(self):
        with self._state_lock:
            self._executing_command = True

    def end_command_execution_mark(self):
        with self._state_lock:
            self._executing_command = False

    def new_operational_state(self, new_state):
        with self._state_lock:
            self._assumed_operational_state = new_state

    def get_operational_state(self):
        with self._state_lock:
            return self._assumed_operational_state

    def get_executing_command(self):
        with self._state_lock:
            return self._executing_command

    def include(self):
        with self._state_lock:
            self._included = True

    def exclude(self):
        with self._state_lock:
            self._included = False

    def included(self):
        with self._state_lock:
            return self._included

    def excluded(self):
        with self._state_lock:
            return not self._included

    def to_error(self):
        with self._state_lock:
            self._errored = True

    def fix_error(self):
        with self._state_lock:
            self._errored = False

    def in_error(self):
        with self._state_lock:
            return self._errored


class ClientSideChild(ChildNode):
    def __init__(self, name, node_type: ControlType = ControlType.Direct, fsm_configuration:FSMConfHandler = None, configuration = None): #
        super().__init__(
            name = name,
            node_type = node_type,
            configuration = configuration
        )

        from logging import getLogger
        self.log = getLogger(f'{name}-client-side')

        self.state = ClientSideState()

        self.fsm_configuration = fsm_configuration

        if fsm_configuration:
            fsmch = FSMConfHandler(fsm_configuration)
            self.fsm = FSM(conf=fsmch)

    def __str__(self):
        return f"'{self.name}' is in error state (type {self.node_type})"

    def terminate(self):
        pass

    def get_endpoint(self):
        pass

    def get_status(self, token):

        status = Status(
            state = self.state.get_operational_state(),
            sub_state = 'idle' if not self.state.get_executing_command() else 'executing_cmd',
            in_error = self.state.in_error() or not self.commander.ping(), # meh
            included = self.state.included(),
        )
        return Response(
            name = self.name,
            token = None,
            data = pack_to_any(status),
            flag = ResponseFlag.EXECUTED_SUCCESSFULLY,
            children = [],
        )

    def propagate_command(self, command:str, data, token:Token) -> Response:
        if command == 'exclude':
            self.state.exclude()
            return Response(
                name = self.name,
                token = token,
                data = pack_to_any(
                    PlainText(
                        text=f"\'{self.name}\' excluded"
                    )
                ),
                flag = ResponseFlag.EXECUTED_SUCCESSFULLY,
                children = []
            )

        elif command == 'include':
            self.state.include()
            return Response(
                name = self.name,
                token = token,
                data = pack_to_any(
                    PlainText(
                        text=f"\'{self.name}\' included"
                    )
                ),
                flag = ResponseFlag.EXECUTED_SUCCESSFULLY,
                children = []
            )

        elif command == 'describe':
            return self.describe(token)

        elif command == 'status':
            return self.get_status(token)

        if self.state.excluded() and command == 'execute_fsm_command':
            return Response(
                name = self.name,
                token = token,
                data = pack_to_any(
                    FSMCommandResponse(
                        flag = FSMResponseFlag.FSM_NOT_EXECUTED_EXCLUDED,
                        command_name = data.command_name,
                        data = None
                    )
                ),
                flag = ResponseFlag.EXECUTED_SUCCESSFULLY,
                children = []
            )

        # here lies the mother of all the problems
        if command == 'execute_fsm_command':
            return self.propagate_fsm_command(command, data, token)

        else:
            self.log.info(f'Ignoring command \'{command}\' sent to \'{self.name}\'')
            return Response(
                name = self.name,
                token = token,
                data = None,
                flag = ResponseFlag.NOT_EXECUTED_NOT_IMPLEMENTED,
                children = []
            )


    def propagate_fsm_command(self, command:str, data, token:Token) -> Response:
        from drunc.exceptions import DruncException
        entry_state = self.state.get_operational_state()
        transition = self.fsm.get_transition(data.command_name)
        exit_state = self.fsm.get_destination_state(entry_state, transition)
        self.state.executing_command_mark()

        response_data = pack_to_any(
            PlainText(
                text = 'successful'
            )
        )

        fsm_data = FSMCommandResponse(
            flag = FSMResponseFlag.FSM_EXECUTED_SUCCESSFULLY,
            command_name = data.command_name,
            data = response_data
        )
        response = Response(
            name = self.name,
            token = token,
            data = pack_to_any(fsm_data),
            flag = ResponseFlag.EXECUTED_SUCCESSFULLY,
            children = {}
        )

        self.state.end_command_execution_mark()
        self.state.new_operational_state(exit_state)
        return response
