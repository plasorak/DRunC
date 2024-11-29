# from enum import StrEnum # I wish, but we need python 3.11 :)
from enum import Enum, auto

from drunc.exceptions import DruncSetupException

class BroadcastTypes(Enum):
    Unknown = auto()
    Kafka = auto()
    ERS = auto()

    @staticmethod
    def from_str(btype:str):
        match btype.lower():
            case 'kafka':
                return BroadcastTypes.Kafka
            case 'ers':
                return BroadcastTypes.ERS
            case _:
                return BroadcastTypes.Unknown


class BroadcastTypeNotHandled(DruncSetupException):
    def __init__(self, btype):
        message = f'{btype} not handled'
        super(BroadcastTypeNotHandled, self).__init__(
            message
        )