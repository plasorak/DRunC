from drunc.fsm.core import FSMAction
import requests
import os 
import json

class UsvcProvidedRunNumber(FSMAction):
    def __init__(self, configuration):
        super().__init__(
            name = "run-number"
        )
        f = open(".drunc.json")
        dotdrunc = json.load(f)
        self.API_SOCKET = dotdrunc["run_number_configuration"]["socket"]
        self.API_USER = dotdrunc["authentication"]["user"]
        self.API_PSWD = dotdrunc["authentication"]["password"]
        self.timeout = 0.5

    def pre_start(self, _input_data:dict, _context, disable_data_storage:bool=False, trigger_rate:float=1.0, **kwargs): #, run_type:str
        _input_data["run"] = self._getnew_run_number()
        _input_data['disable_data_storage'] = disable_data_storage
        _input_data['trigger_rate'] = trigger_rate
        return _input_data

    def _getnew_run_number(self):
        from drunc.fsm.exceptions import CannotGetRunNumber
        try:
            req = requests.get(self.API_SOCKET+'/runnumber/getnew',
                               auth=(self.API_USER, self.API_PSWD),
                               timeout=self.timeout)
            req.raise_for_status()
        except requests.HTTPError as exc:
            error = f"{__name__}: HTTP Error (maybe failed auth, maybe ill-formed post message, ...)"
            self.log.error(error)
            raise CannotGetRunNumber(error) from exc
        except requests.ConnectionError as exc:
            error = f"{__name__}: Connection to {self.API_SOCKET} wasn't successful"
            self.log.error(error)
            raise CannotGetRunNumber(error) from exc
        except requests.Timeout as exc:
            error = f"{__name__}: Connection to {self.API_SOCKET} timed out"
            self.log.error(error)
            raise CannotGetRunNumber(error) from exc

        self.run = req.json()[0][0][0]
        return self.run