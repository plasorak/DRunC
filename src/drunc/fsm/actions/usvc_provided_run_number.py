import json
import os
import requests

from drunc.fsm.actions.utils import validate_run_type
from drunc.fsm.core import FSMAction
from drunc.fsm.exceptions import CannotGetRunNumber
from drunc.utils.utils import expand_path, get_logger


class UsvcProvidedRunNumber(FSMAction):
    def __init__(self, configuration):
        super().__init__(
            name = "usvc-provided-run-number"
        )
        f = open(expand_path("~/.drunc.json")) # cp /nfs/home/titavare/dunedaq_work_area/drunc-n24.5.26-1/.drunc.json
        dotdrunc = json.load(f)
        self.API_SOCKET = dotdrunc["run_number_configuration"]["socket"]
        self.API_USER = dotdrunc["run_number_configuration"]["user"]
        self.API_PSWD = dotdrunc["run_number_configuration"]["password"]
        self.timeout = 0.5

        self.log = get_logger('microservice')

    def pre_start(self, _input_data:dict, _context, run_type:str="TEST", disable_data_storage:bool=False, trigger_rate:float=0., **kwargs):
        run_type = validate_run_type(run_type.upper())
        _input_data['production_vs_test'] = run_type
        _input_data["run"] = self._getnew_run_number()
        _input_data['disable_data_storage'] = disable_data_storage
        _input_data['trigger_rate'] = trigger_rate
        return _input_data

    def _getnew_run_number(self):
        try:
            req = requests.get(self.API_SOCKET+"/runnumber/getnew",
                               auth=(self.API_USER, self.API_PSWD),
                               timeout=self.timeout)
            req.raise_for_status()
        except requests.HTTPError as exc:
            error = f"of HTTP Error (maybe failed auth, maybe ill-formed post message, ...) using {__name__}"
            self.log.error(error)
            raise CannotGetRunNumber(error) from exc
        except requests.ConnectionError as exc:
            error = f"connection to {self.API_SOCKET} wasn't successful using {__name__}"
            self.log.error(error)
            raise CannotGetRunNumber(error) from exc
        except requests.Timeout as exc:
            error = f"connection to {self.API_SOCKET} timed out using {__name__}"
            self.log.error(error)
            raise CannotGetRunNumber(error) from exc

        self.run = req.json()[0][0][0]
        return self.run