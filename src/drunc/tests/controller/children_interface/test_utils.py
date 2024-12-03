import pytest
from socket import gethostbyname, gethostname

from drunc.exceptions import DruncSetupException
from drunc.controller.children_interface.utils import get_control_type_and_uri_from_cli
from drunc.controller.children_interface.types import ControlType

def test_get_control_type_and_uri_from_cli():

    this_address = gethostbyname(gethostname())+":1234"
    def generate_cli(control_type, uri):
        return [f"{control_type}://{uri}:1234", "--something-else", "--drunc"]

    control_type, uri = get_control_type_and_uri_from_cli(generate_cli("grpc", "localhost"))
    assert control_type == ControlType.gRPC
    assert uri == this_address

    control_type, uri = get_control_type_and_uri_from_cli(generate_cli("grpc", "0.0.0.0"))
    assert control_type == ControlType.gRPC
    assert uri == this_address

    control_type, uri = get_control_type_and_uri_from_cli(generate_cli("grpc", "np04-srv-123"))
    assert control_type == ControlType.gRPC
    assert uri == "np04-srv-123:1234"

    control_type, uri = get_control_type_and_uri_from_cli(generate_cli("rest", "localhost"))
    assert control_type == ControlType.REST_API
    assert uri == this_address

    control_type, uri = get_control_type_and_uri_from_cli(generate_cli("rest", "0.0.0.0"))
    assert control_type == ControlType.REST_API
    assert uri == this_address

    control_type, uri = get_control_type_and_uri_from_cli(generate_cli("rest", "np04-srv-123"))
    assert control_type == ControlType.REST_API
    assert uri == "np04-srv-123:1234"

    with pytest.raises(DruncSetupException):
        get_control_type_and_uri_from_cli(generate_cli("restt", "bla"))
