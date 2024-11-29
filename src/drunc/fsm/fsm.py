from confmodel import get_states
from inspect import Parameter, signature
from logging import getLogger
import traceback

# Good ol' moo import
from dunedaq.env import get_moo_model_path
import moo.io
moo.io.default_load_path = get_moo_model_path()
import moo.otypes
import moo.oschema as moosc
moo.otypes.load_types('rcif/cmd.jsonnet')
moo.otypes.load_types('cmdlib/cmd.jsonnet')
import dunedaq.rcif.cmd as rccmd
import dunedaq.cmdlib.cmd as cmd

from druncschema.controller_pb2 import Argument
from druncschema.generic_pb2 import NullValue

import drunc.fsm.exceptions as fsme
from drunc.fsm.transition import Transition, TransitionSequence
from drunc.fsm.utils import get_underlying_schema
from drunc.utils.configuration import ConfigurationWrapper
from drunc.utils.utils import regex_match

class Callback:
    def __init__(self, method, mandatory=True):
        self.method = method
        self.mandatory = mandatory


class FSM:
    def __init__(self, conf:ConfigurationWrapper):

        self.configuration = conf

        self._log = getLogger('FSM')

        self.initial_state = self.configuration.dal.initial_state

        self.states = get_states(self.configuration.db_obj, self.configuration.dal.id)

        self.transitions = self._build_transitions(self.configuration.dal.transitions)


    def _build_arguments_from_rcif(self, rcif_schema:str) -> [Argument]:
        if rcif_schema == "":
            return []

        self._log.debug(f'Parsing the rcif_schema: \'{rcif_schema}\'')

        schema = getattr(rccmd, rcif_schema, None)
        if schema is None:
            raise fsme.SchemaNotSupportedByRCIF(rcif_schema)

        arguments = []

        for field in schema.__dict__["_ost"]["fields"]:
            self._log.debug(f" - field {field}")
            arg_type = get_underlying_schema(field)
            self._log.debug(f"   ... of type \'{arg_type}\'")

            arg_kwargs = {
                "name": field['name'],
                "type": arg_type,
                "help": field['doc'],
                "mandatory": not field.get('optional', False),
            }

            if 'choices' in field:
                arg_kwargs.update({
                    f"{arg_type}_choices": field['choices'],
                })

            if 'default' in field:
                arg_kwargs.update({
                    f"{arg_type}_default": field['default'],
                })

            a = Argument(**arg_kwargs)

            self._log.debug(f"Argument produced:\n{a}")
            default_arg = getattr(a, arg_type+"_default")
            arguments += [a]
        return arguments


    def _build_one_transition(self, transition) -> Transition:
        arguments = self._build_arguments_from_rcif(transition.rcif_schema)

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

        return retr.values()


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
