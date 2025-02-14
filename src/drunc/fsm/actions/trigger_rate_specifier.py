import json
import os
import requests
import tempfile
import tarfile

from drunc.fsm.core import FSMAction


class TriggerRateSpecifier(FSMAction):
    def __init__(self, configuration):
        super().__init__(
            name = "trigger-rate-specifier"
        )

    def pre_change_rate(self, _input_data:dict, _context, trigger_rate:float, **kwargs):
        _input_data["trigger_rate"] = trigger_rate
        return _input_data


