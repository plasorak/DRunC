# https://github.com/DUNE-DAQ/drunc/issues/309

from drunc.controller.configuration import ControllerConfHandler
from drunc.tests.issues.issue_fixtures import load_test_config

def test_issue309(load_test_config):
    from drunc.utils.configuration import parse_conf_url, OKSKey
    import os
    print(f"{os.getenv('DUNEDAQ_DB_PATH')=}")
    conf_path, conf_type = parse_conf_url(f'oksconflibs://issue309.data.xml')
    controller_id = "controller-3"
    controller_configuration = ControllerConfHandler(
        type = conf_type,
        data = conf_path,
        oks_key = OKSKey(
            schema_file = 'schema/confmodel/dunedaq.schema.xml',
            class_name = "RCApplication",
            obj_uid = controller_id,
            session = "deep-segments-config", # some of the function for enable/disable require the full dal of the session
        ),
    )

    assert(controller_configuration.data.controller.id == controller_id)