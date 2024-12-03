import pytest

from drunc.fsm import FSM, Transition, TransitionSequence, NoTransitionOfName
from drunc.tests.fixtures.configuration import load_test_config
from drunc.utils.configuration import ConfigurationWrapper

def test_fsm(load_test_config):
    try:
        import conffwk
    except ImportError:
        pytest.skip('conffwk not installed')
    db = conffwk.Configuration('oksconflibs:fsm.data.xml')
    fsm_dal = db.get_dal(class_name='FSM', uid="fsm-daq")
    fsm_conf = ConfigurationWrapper(db._obj, fsm_dal)
    fsm = FSM(fsm_conf)

    assert fsm.initial_state == fsm_dal.initial_state

    assert fsm.get_all_states() == set([
        'initial',
        'configured',
        'running',
        'ready',
        'dataflow_drained',
        'trigger_sources_stopped',
    ])

    assert len(fsm.get_all_transitions()) == 12

    with pytest.raises(NoTransitionOfName):
        fsm.get_transition_from_str('not_a_transition')

    assert fsm.get_transition_from_str('conf'                ).name == 'conf'
    assert fsm.get_transition_from_str('start'               ).name == 'start'
    assert fsm.get_transition_from_str('enable_triggers'     ).name == 'enable_triggers'
    assert fsm.get_transition_from_str('disable_triggers'    ).name == 'disable_triggers'
    assert fsm.get_transition_from_str('drain_dataflow'      ).name == 'drain_dataflow'
    assert fsm.get_transition_from_str('stop_trigger_sources').name == 'stop_trigger_sources'
    assert fsm.get_transition_from_str('stop'                ).name == 'stop'
    assert fsm.get_transition_from_str('scrap'               ).name == 'scrap'
    assert fsm.get_transition_from_str('change_rate'         ).name == 'change_rate'
    assert fsm.get_transition_from_str('change_rate'         ).name == 'change_rate'



    with pytest.raises(NoTransitionOfName):
        fsm.get_destination_state('initial', 'not_a_transition')

    assert fsm.get_destination_state('initial'                , 'conf'                ) == 'configured'
    assert fsm.get_destination_state('configured'             , 'start'               ) == 'ready'
    assert fsm.get_destination_state('ready'                  , 'enable_triggers'     ) == 'running'
    assert fsm.get_destination_state('running'                , 'disable_triggers'    ) == 'ready'
    assert fsm.get_destination_state('ready'                  , 'drain_dataflow'      ) == 'dataflow_drained'
    assert fsm.get_destination_state('dataflow_drained'       , 'stop_trigger_sources') == 'trigger_sources_stopped'
    assert fsm.get_destination_state('trigger_sources_stopped', 'stop'                ) == 'configured'
    assert fsm.get_destination_state('configured'             , 'scrap'               ) == 'initial'
    assert fsm.get_destination_state('ready'                  , 'change_rate'         ) == 'ready'
    assert fsm.get_destination_state('running'                , 'change_rate'         ) == 'running'



