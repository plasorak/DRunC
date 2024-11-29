from typing import Optional

from druncschema.broadcast_pb2 import BroadcastType

from drunc.broadcast.server.broadcast_sender import BroadcastSender
from drunc.stateful.observable import OperationalState, ErrorState, InclusionState
from drunc.fsm import FSM, InvalidTransition

class Stateful:
    def __init__(self, fsm_configuration, broadcaster:Optional[BroadcastSender]=None):

        self.broadcast = broadcaster

        self.__fsm = FSM(fsm_configuration)

        from logging import getLogger
        self.logger = getLogger('StatefulNode')

        self.__operational_state = OperationalState(
            broadcast_on_change = self.broadcast,
            broadcast_key = BroadcastType.FSM_STATUS_UPDATE,
            initial_value = self.__fsm.initial_state
        )
        self.__operational_sub_state = OperationalState(
            broadcast_on_change = self.broadcast,
            broadcast_key = BroadcastType.FSM_STATUS_UPDATE,
            initial_value = self.__fsm.initial_state
        )
        self.__included = InclusionState(
            broadcast_on_change = self.broadcast,
            broadcast_key = BroadcastType.STATUS_UPDATE,
            initial_value = True
        )
        self.__in_error = ErrorState(
            broadcast_on_change = self.broadcast,
            broadcast_key = BroadcastType.STATUS_UPDATE,
            initial_value = False
        )

    def get_node_operational_state(self):
        return self.__operational_state.value

    def get_node_operational_sub_state(self):
        return self.__operational_sub_state.value

    def get_fsm_transitions(self):
        r = self.__fsm.get_executable_transitions(self.get_node_operational_state())
        return r

    def get_all_fsm_transitions(self):
        r = self.__fsm.get_all_transitions()
        return r

    def get_fsm_transition(self, transition_name):
        return self.__fsm.get_transition(transition_name)

    def include_node(self):
        if self.__included.value:
            raise CannotInclude()
        self.__included.value = True

    def exclude_node(self):
        if not self.__included.value:
            raise CannotExclude()
        self.__included.value = False

    def node_is_included(self):
        return self.__included.value

    def to_error(self):
        self.__in_error.value = True

    def resolve_error(self):
        self.__in_error.value = False

    def node_is_in_error(self):
        return self.__in_error.value

    def can_transition(self, transition):
        self.logger.debug(f'{self.__operational_state.value} == {self.__operational_sub_state.value} ?')
        if self.__operational_state.value != self.__operational_sub_state.value:
            return False
        return self.__fsm.can_execute_transition(self.get_node_operational_state(), transition)

    def decode_fsm_arguments(self, fsm_command):
        from drunc.fsm.utils import decode_fsm_arguments
        transition = self.get_fsm_transition(fsm_command.command_name)
        return decode_fsm_arguments(fsm_command.arguments, transition.arguments)

    def prepare_transition(self, transition, transition_data, transition_args, ctx=None):
        if self.get_node_operational_state() != self.get_node_operational_sub_state():
            raise InvalidSubTransition(self.get_node_sub_operational_state(), self.get_node_operational_state(), 'prepare_transition')

        if not self.__fsm.can_execute_transition(self.get_node_operational_state(), transition):
            raise InvalidTransition(transition, self.get_node_operational_state())

        self.__operational_sub_state.value = f'preparing-{transition.name}'

        transition_data = self.__fsm.prepare_transition(
            transition,
            transition_data,
            transition_args,
            ctx,
        )

        self.__operational_sub_state.value = f'{transition.name}-ready'

        return transition_data

    def propagate_transition_mark(self, transition):

        if self.get_node_operational_sub_state() != f'{transition.name}-ready':
            raise InvalidSubTransition(self.get_node_operational_sub_state(), f'{transition.name}-ready', 'propagate_transition')

        self.__operational_sub_state.value = f'propagating-{transition.name}'


    def finish_propagating_transition_mark(self, transition):

        if self.get_node_operational_sub_state() != f'propagating-{transition.name}':
            raise InvalidSubTransition(self.get_node_operational_sub_state(), f'propagating-{transition.name}', 'finish_propagating_transition')

        self.__operational_sub_state.value = f'{transition.name}-propagated'


    def start_transition_mark(self, transition):

        if self.get_node_operational_sub_state() != f'{transition.name}-propagated':
            raise InvalidSubTransition(self.get_node_operational_sub_state(), f'{transition.name}-propagated', 'start_transition')

        self.__operational_sub_state.value = f'executing-{transition.name}'


    def terminate_transition_mark(self, transition):

        if self.get_node_operational_sub_state() != f'executing-{transition.name}':
            raise InvalidSubTransition(self.get_node_operational_sub_state(), f'executing-{transition.name}', 'terminate_transition')

        self.__operational_sub_state.value = f'{transition.name}-terminated'
        self.__operational_state.value = self.__fsm.get_destination_state(self.__operational_state.value, transition)


    def finalise_transition(self, transition, transition_data, transition_args, ctx=None):

        if self.get_node_operational_sub_state() != f'{transition.name}-terminated':
            raise InvalidSubTransition(self.get_node_operational_sub_state(), f'{transition.name}-terminated', 'finalise_transition')

        self.__operational_sub_state.value = f'finalising-{transition.name}'
        transition_data = self.__fsm.finalise_transition(
            transition,
            transition_data,
            transition_args,
            ctx,
        )
        self.__operational_sub_state.value = self.__operational_state.value

        return transition_data