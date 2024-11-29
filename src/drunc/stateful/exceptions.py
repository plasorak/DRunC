from drunc.exceptions import DruncCommandException
class StatefulNodeException(DruncCommandException):
    pass

class CannotInclude(StatefulNodeException):
    def __init__(self):
        super().__init__('Cannot include node (most likely, it is already included)')

class CannotExclude(StatefulNodeException):
    def __init__(self):
        super().__init__('Cannot exclude node (most likely, it is already excluded)')

class InvalidSubTransition(StatefulNodeException):
    def __init__(self, current_state, expected_state, action):
        message = f'SubTransition "{action}" cannot be executed, state needs to be "{expected_state}", it is now "{current_state}"'
        super(InvalidSubTransition, self).__init__(message)

class TransitionNotTerminated(StatefulNodeException):
    def __init__(self):
        super().__init__('The transition did not finished successfully')

class TransitionExecuting(StatefulNodeException):
    def __init__(self):
        super().__init__('A transition is already executing')