from typing import Optional
from drunc.broadcast.server.broadcast_sender import BroadcastSender

class Observed:
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if self._broadcast_on_change is None or self._broadcast_key is None:
            self._value = value
            return

        self._broadcast_on_change.broadcast(
            message = f'Changing {self._name} from {self._value} to {value}',
            btype = self._broadcast_key,
        )
        self._value = value

    def __init__(
            self,
            name:str,
            broadcast_on_change:Optional[BroadcastSender]=None,
            broadcast_key=None, # Optional[BroadcastType]=None
            initial_value:Optional[str]=None
        ):
        self._name = name
        self._broadcast_on_change = broadcast_on_change
        self._value = initial_value
        self._broadcast_key = broadcast_key


class OperationalState(Observed):
    def __init__(self, **kwargs):
        super(OperationalState, self).__init__(
            name = 'operational_state',
            **kwargs
        )


class ErrorState(Observed):
    def __init__(self, **kwargs):
        super(ErrorState, self).__init__(
            name = 'error_state',
            **kwargs
        )


class InclusionState(Observed):
    def __init__(self, **kwargs):
        super(InclusionState, self).__init__(
            name = 'inclusion_state',
            **kwargs
        )
