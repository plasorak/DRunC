
import json
import os
import requests

from drunc.fsm.core import FSMAction
from drunc.fsm.exceptions import CannotSendElisaMessage
from drunc.utils.configuration import find_configuration
from drunc.utils.utils import expand_path, get_logger


class ElisaLogbook(FSMAction):
    def __init__(self, configuration):
        super().__init__(name = "elisa-logbook")

        f = open(expand_path("~/.drunc.json"))
        dotdrunc = json.load(f)
        self.API_SOCKET = dotdrunc["elisa_configuration"]["socket"]
        self.API_USER =  dotdrunc["elisa_configuration"]["user"]
        self.API_PASS =  dotdrunc["elisa_configuration"]["password"]
        self.timeout = 5
        self.log = get_logger('controller.usvc_Elisa')

    def post_start(self, _input_data:dict, _context, elisa_post:str='', **kwargs):
        text = ""
        self.thread_id = None    #Clear this value here, so that if it fails stop can't reply to an old message

        self.run_num = _input_data['run']
        if elisa_post != '':
            self.log.info(f"Adding the message:\n--------\n{elisa_post}\n--------\nto the logbook")
            text += f"\n<p>{elisa_post}</p>"

        self.run_type = _input_data.get('run_type', "TEST")    #This class won't exist in a test run, so we're adding this temporarily so that we can actually run the function
        run_configuration = find_configuration(_context.configuration.initial_data)
        text += f"Configuration: {run_configuration}"

        if elisa_post != '' and self.run_type.lower() != 'prod':
            self.log.warning('Your message will NOT be stored, as this is not a PROD run')

        text += "\n<p>log automatically generated by DRunC.</p>"
        self.det_id = _context.configuration.db.get_dal(class_name = "Session", uid = _context.configuration.oks_key.session).detector_configuration.id
        title = f"Run {self.run_num} ({self.run_type}) started on {self.det_id}"
        data = {"author":_context.actor.get_user_name(), "title":title, "body":text, "command":"start", "systems":["daq"]}
        url = f"{self.API_SOCKET}/v1/elisaLogbook/new_message/"
        try:
            r = requests.post(url, auth=(self.API_USER,self.API_PASS), json=data)
            r.raise_for_status()
            response = r.json()
            self.thread_id = response['thread_id']
            self.log.info(f"ELisA logbook: Sent message (ID{self.thread_id})")
        except requests.HTTPError as exc:
            error = f"of HTTP Error (maybe failed auth, maybe ill-formed post message, ...) using {__name__}"
            self.log.warning(CannotSendElisaMessage(error).message)
        except requests.ConnectionError as exc:
            error = f"connection to {self.API_SOCKET} wasn't successful using {__name__}"
            self.log.warning(CannotSendElisaMessage(error).message)
        except requests.Timeout as exc:
            error = f"connection to {self.API_SOCKET} timed out using {__name__}"
            self.log.warning(CannotSendElisaMessage(error).message)

        return _input_data

    def post_drain_dataflow(self, _input_data, _context, elisa_post:str='', **kwargs):
        text = ''
        if elisa_post != '':
            self.log.info(f"Adding the message:\n--------\n{elisa_post}\n--------\nto the logbook")
            text += f"\n<p>{elisa_post}</p>"

        text += f"Run {self.run_num} ({self.run_type}) stopped on {self.det_id}"
        text += "\n<p>log automatically generated by DRunC.</p>"
        title = "User comment"
        data = {"author":_context.actor.get_user_name(), "title":title, "body":text, "command":"stop", "systems":["daq"], "id":self.thread_id}
        url = f'{self.API_SOCKET}/v1/elisaLogbook/reply_to_message/'
        try:
            r = requests.put(url, auth=(self.API_USER,self.API_PASS), json=data)
            r.raise_for_status()
            response = r.json()
            self.log.info(f"ELisA logbook: Sent message (ID{response['thread_id']})")
        except requests.HTTPError as exc:
            error = f"of HTTP Error (maybe failed auth, maybe ill-formed post message, ...) using {__name__}"
            self.log.warning(CannotSendElisaMessage(error).message)
        except requests.ConnectionError as exc:
            error = f"connection to {self.API_SOCKET} wasn't successful using {__name__}"
            self.log.warning(CannotSendElisaMessage(error).message)
        except requests.Timeout as exc:
            error = f"connection to {self.API_SOCKET} timed out using {__name__}"
            self.log.warning(CannotSendElisaMessage(error).message)

        return _input_data
