from enum import Enum
from drunc.exceptions import DruncSetupException


class BroadcastTypes(Enum):
    Unknown = 0
    Kafka = 1
    ERS = 2


class BroadcastTypeNotHandled(DruncSetupException):
    def __init__(self, btype):
        message = f'{btype} not handled'
        super(BroadcastTypeNotHandled, self).__init__(
            message
        )