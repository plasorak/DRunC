from confmodel import get_states
from inspect import Parameter, signature
from logging import getLogger
import traceback
from typing import Union

from druncschema.controller_pb2 import Argument
from druncschema.generic_pb2 import NullValue

import drunc.fsm.exceptions as fsme
from drunc.fsm.transition import Transition, TransitionSequence
from drunc.fsm.utils import build_arguments_from_rcif
from drunc.utils.configuration import ConfigurationWrapper
from drunc.utils.utils import regex_match


class FSM:
    def __init__(self, conf:ConfigurationWrapper):

        self.configuration = conf

        self._log = getLogger('drunc.FSM')

        self.initial_state = self.configuration.dal.initial_state

        self.states = get_states(self.configuration.db_obj, self.configuration.dal.id)

        self.transitions = self._build_transitions(self.configuration.dal.transitions)


    def _build_one_transition(self, transition) -> Transition:
        arguments = build_arguments_from_rcif(transition.rcif_schema)

        return Transition(
            name = transition.id,
            source = transition.source,
            destination = transition.dest,
            arguments = arguments,
        )


    def _build_transition_set(self, transition_set) -> (TransitionSequence, [Transition]):
        all_transitions = []
        for t in transition_set.sequence:
            all_transitions += [self._build_one_transition(t)]
        return TransitionSequence(transition_set.id, transitions = all_transitions), all_transitions


    def _build_transitions(self, transitions:[]) -> [Transition]:
        '''
        Builds the transitions
        '''
        the_drunc_transitions = []

        for t in transitions:
            self._log.debug(f'Considering transition: \'{t.id}\'')

            match t.className():
                case 'FSMTransition':
                    the_drunc_transitions += [self._build_one_transition(t)]

                case 'FSMTransitionSet':
                    transition_sequence, transitions = self._build_transition_set(t)
                    the_drunc_transitions += transitions
                    the_drunc_transitions += [transition_sequence]

                case _:
                    self._log.error(t.className())
                    raise fsme.UnhandledTransitionType(t.id, t.className())

        retr = {}
        for the_drunc_transition in the_drunc_transitions:
            retr[the_drunc_transition.name] = the_drunc_transition

        return list(retr.values())


    def get_all_states(self) -> [str]:
        return self.states


    def get_all_transitions(self) -> [Transition]:
        return self.transitions


    def get_destination_state(self, source_state:str, transition:Union[str,Transition]) -> str:
        if isinstance(transition, str):
            transition = self.get_transition_from_str(transition)

        if self.can_execute_transition(source_state, transition):
            if tr.destination == "":
                return source_state
            else:
                return tr.destination

        raise fsme.CannotExecuteTransition(source_state, transition.name)


    def get_executable_transitions(self, source_state:str) -> [Transition]:
        valid_transitions = []

        for tr in self.transitions:
            debug_txt = f'Testing if transition {str(tr)} is executable from state "{source_state}"...'
            if self.can_execute_transition(source_state, tr):
                self._log.debug(f'{debug_txt} Yes')
                valid_transitions.append(tr)
            else:
                self._log.debug(f'{debug_txt} No')

        return valid_transitions


    def get_transition_from_str(self, transition_name:str) -> Transition:
        transitions = [t for t in self.transitions if t.name.lower() == transition_name.lower()]
        print(transitions)
        if not transitions:
            fsme.NoTransitionOfName(transition_name)

        return transitions[0]


    def can_execute_transition(self, source_state:str, transition:Union[str,Transition]) -> bool:
        return regex_match(transition.source, source_state)
