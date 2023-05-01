from drunc.fsm.fsm_core import FSMPlugin

class LogbookPlugin(FSMPlugin):
    def __init__(self, configuration):
        super().__init__("logbook")

    def post_start(self, data):
        print(f"Running post-start of {self.name}")