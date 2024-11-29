from druncschema.controller_pb2 import Argument

class Transition:
    def __init__(self, name:str, source:str, destination:str, arguments:[Argument]=[], help:str=''):
        self.source = source
        self.destination = destination
        self.name = name
        self.arguments = arguments
        self.help = help


    def __eq__(self, another):
        same_name = hasattr(another, 'name') and self.name == another.name
        same_destination = hasattr(another, 'destination') and self.destination == another.destination
        same_source = hasattr(another, 'source') and self.source == another.source
        return same_name and same_destination and same_source

    def __hash__(self):
        return hash(self.__str__())

    def __str__(self):
        return f'\"{self.name}\": \"{self.source}\" → \"{self.destination}\"'

    def get_arguments(self):
        return self.arguments

class TransitionSequence(Transition):
    def __init__(self, name:str, transitions:[Transition]=[]):
        self.sequence = transitions
        help_str = 'A sequence of transtions:\n'+'\n'.join([f' - {t.name}: {t.help}' for t in transitions])
        dest = transitions[-1].destination
        source = '|'.join([t.source for t in transitions])
        arguments = []
        for t in transitions:
            arguments += t.get_arguments()

        super().__init__(name, source, dest, arguments, help=help_str)

