from drunc.fsm.core import FSMAction
from opmonlib.opmon.test_pb2 import TestInfo


class UserProvidedRunNumber(FSMAction):
    def __init__(self, configuration):
        super().__init__(
            name = "run-number"
        )

    def pre_start(self, _input_data:dict, _context, run_number:int, disable_data_storage:bool=False, trigger_rate:float=0., run_type:str='TEST', **kwargs):
        from drunc.fsm.actions.utils import validate_run_type
        run_type = validate_run_type(run_type.upper())
        _input_data['production_vs_test'] = run_type
        _input_data["run"] = run_number
        _input_data['disable_data_storage'] = disable_data_storage
        _input_data['trigger_rate'] = trigger_rate

        message = init_simple_msg(
            test_string=run_type, 
            test_float=trigger_rate,
            test_int=run_number, 
            test_bool=disable_data_storage
            )
        
        _context.publisher.publish(
                session="test_runnumber_session",
                application="test_runnumber_app",
                message=message
            )

        return _input_data


def init_simple_msg(test_string = "kafkaopmon_drunc_python_test_runnumber",
    test_float = 123.456789,
    test_int = 0,
    test_bool = False) -> TestInfo:

    test_info = TestInfo(
        string_example=test_string,
        float_example=test_float,
        int_example=test_int,
        bool_example=test_bool
    )
    return test_info