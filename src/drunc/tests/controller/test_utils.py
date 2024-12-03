import os
import pytest

from drunc.controller.utils import get_segment_lookup_timeout
from drunc.tests.fixtures.configuration import load_test_config

def test_get_segment_lookup_timeout(load_test_config):
    try:
        import conffwk
    except ImportError:
        pytest.skip('conffwk not installed')

    db = conffwk.Configuration('oksconflibs:many-recursive-segments.data.xml')

    segment_0 = db.get_dal(class_name='Segment', uid="segment-0")
    assert get_segment_lookup_timeout(segment_0, base_timeout=60) == 60*5

    segment_1 = db.get_dal(class_name='Segment', uid="segment-1")
    assert get_segment_lookup_timeout(segment_1, base_timeout=60) == 60*4

    segment_2 = db.get_dal(class_name='Segment', uid="segment-2")
    assert get_segment_lookup_timeout(segment_2, base_timeout=60) == 60*2

    segment_3 = db.get_dal(class_name='Segment', uid="segment-3")
    assert get_segment_lookup_timeout(segment_3, base_timeout=60) == 60*1

    segment_4 = db.get_dal(class_name='Segment', uid="segment-4")
    assert get_segment_lookup_timeout(segment_4, base_timeout=60) == 60*3

    segment_5 = db.get_dal(class_name='Segment', uid="segment-5")
    assert get_segment_lookup_timeout(segment_5, base_timeout=60) == 60*2

    segment_6 = db.get_dal(class_name='Segment', uid="segment-6")
    assert get_segment_lookup_timeout(segment_6, base_timeout=60) == 60*1
