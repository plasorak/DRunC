from confmodel import get_states
from inspect import Parameter, signature
from logging import getLogger
import traceback

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

        self._log = getLogger('FSM')

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
        '''
        grabs all the states
        '''
        return self.states


    def get_all_transitions(self) -> [Transition]:
        '''
        grab all the transitions
        '''
        return self.transitions


    def get_destination_state(self, source_state:str, transition:Transition) -> str:
        '''
        Tells us where a particular transition will take us, given the source_state
        '''
        right_name = [t for t in self.transitions if t == transition]
        for tr in right_name:
            if self.can_execute_transition(source_state, transition):
                if tr.destination == "":
                    return source_state
                else:
                    return tr.destination


    def get_executable_transitions(self, source_state:str) -> [Transition]:
        valid_transitions = []

        for tr in self.transitions:
            debug_txt = f'Testing if transition {str(tr)} is executable from state "{source_state}"...'
            if self.can_execute_transition(source_state, tr):
                self._log.debug(f'{debug_txt} Yes')
                valid_transitions.append(tr)
            else:
                self._log.debug(f'{debug_txt} No\n')

        return valid_transitions


    def get_transition(self, transition_name:str) -> bool:
        transition = [t for t in self.transitions if t.name == transition_name]
        if not transition:
            fsme.NoTransitionOfName(transition_name)
        return transition[0]


    def can_execute_transition(self, source_state:str, transition:Transition) -> bool:
        '''
        Check that this transition is allowed given the source_state
        '''
        self._log.debug(f'can_execute_transition {str(transition.source)} {source_state}')
        return regex_match(transition.source, source_state)


    def prepare_transition(self, transition:Transition, transition_data:dict, transition_args:dict, ctx:dict=None):
        transition_data = self.pre_transition_sequences[transition].execute(
            transition_data,
            transition_args,
            ctx
        )
        return transition_data


    def finalise_transition(self, transition:Transition, transition_data:dict, transition_args:dict, ctx:dict=None):
        transition_data = self.post_transition_sequences[transition].execute(
            transition_data,
            transition_args,
            ctx
        )
        return transition_data
