import abc
from typing import Callable

from druncschema.controller_pb2 import Argument

class RCAction(abc.ABC):
    def __init__(self):
        pass

    @abc.abstractmethod
    def callback(self, transition_id:str) -> Callable:
        '''
        This method should return a callable that will be executed when the transition is triggered.
        '''
        pass

    @abc.abstractmethod
    def provides_data(self, transition_id:str) -> [Argument]:
        '''
        This method should return a list of arguments that the action will provide, for the transition on which it will run.
        '''
        pass

    @abc.abstractmethod
    def requires_argument(self, transition_id:str) -> [Argument]:
        '''
        This method should return a list of arguments that the action will require, for the transition on which it will run. Note the this arguments can be provided by other actions.
        '''
        pass