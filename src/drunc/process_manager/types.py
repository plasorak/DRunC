from enum import Enum

class ProcessManagerTypes(Enum):
    Unknown = 0
    SSH = 1
    K8s = 2

    @staticmethod
    def from_str(pmtype:str):
        match pmtype.lower():
            case 'ssh':
                return ProcessManagerTypes.SSH
            case 'k8s':
                return ProcessManagerTypes.K8s
            case _:
                return ProcessManagerTypes.Unknown
