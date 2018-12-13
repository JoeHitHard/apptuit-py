"""
Tests on Apptuit class
"""
import os
from nose.tools import assert_equals, assert_raises
from pyformance import MetricsRegistry

from apptuit.apptuit_client import APPTUIT_API_TOKEN, APPTUIT_PY_TAGS, _get_tags_from_environment

from apptuit import Apptuit, DataPoint
from apptuit.pyformance import ApptuitReporter

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch

def test_token_positive():
    """
        Test that token is working normally
    """
    mock_environ = patch.dict(os.environ, {APPTUIT_API_TOKEN: "environ_token"})
    mock_environ.start()
    client = Apptuit()
    assert_equals(client.token, "environ_token")
    client = Apptuit(token="")
    assert_equals(client.token, "environ_token")
    client = Apptuit(token=None)
    assert_equals(client.token, "environ_token")
    client = Apptuit(token="argument_token")
    assert_equals(client.token, "argument_token")
    mock_environ.stop()

def test_token_negative():
    """
        Test that invalid token raises error
    """
    mock_environ = patch.dict(os.environ, {})
    mock_environ.start()
    with assert_raises(ValueError) as m:
        Apptuit()
    with assert_raises(ValueError) as m:
        Apptuit(token="")
    with assert_raises(ValueError) as m:
        Apptuit(token=None)
    mock_environ.stop()

def test_tags_positive():
    """
        Test that tags work normally
    """
    mock_environ = patch.dict(os.environ, {APPTUIT_API_TOKEN: "environ_token",
                                           APPTUIT_PY_TAGS: 'tagk1:22,tagk2:tagv2'})
    mock_environ.start()
    client = Apptuit()
    assert_equals(client._environ_tags, {"tagk1": "22", "tagk2": "tagv2"})
    mock_environ.stop()

def test_tags_negative():
    """
        Test that invalid tag raises error
    """
    mock_environ = patch.dict(os.environ, {APPTUIT_API_TOKEN: "environ_token"})
    mock_environ.start()
    client = Apptuit()
    assert_equals({}, client._environ_tags)
    mock_environ.stop()
    mock_environ = patch.dict(os.environ, {APPTUIT_API_TOKEN: "environ_token", APPTUIT_PY_TAGS: "{InvalidTags"})
    mock_environ.start()
    assert_equals({}, client._environ_tags)
    mock_environ.stop()
    mock_environ = patch.dict(os.environ, {APPTUIT_API_TOKEN: "environ_token", APPTUIT_PY_TAGS: '"tagk1":"tagv1"'})
    mock_environ.start()
    with assert_raises(ValueError):
        Apptuit()
    mock_environ.stop()

def test_datapoint_tags_take_priority():
    """
        Test that datapoint tags take priority
    """
    mock_environ = patch.dict(os.environ, {APPTUIT_API_TOKEN: "environ_token",
                                           APPTUIT_PY_TAGS: 'host: host1, ip: 1.1.1.1'})
    mock_environ.start()
    client = Apptuit()
    test_val = 123
    dp1 = DataPoint("test_metric", {"host": "host2", "ip": "2.2.2.2", "test": 1}, test_val, test_val)
    dp2 = DataPoint("test_metric", {"test": 2}, test_val, test_val)
    dp3 = DataPoint("test_metric", {}, test_val, test_val)
    payload = client._create_payload([dp1, dp2, dp3])
    assert_equals(len(payload), 3)
    assert_equals(payload[0]["tags"], {"host": "host2", "ip": "2.2.2.2", "test": 1})
    assert_equals(payload[1]["tags"], {"host": "host1", "ip": "1.1.1.1", "test": 2})
    assert_equals(payload[2]["tags"], {"host": "host1", "ip": "1.1.1.1"})
    assert_equals(client._environ_tags, {"host": "host1", "ip": "1.1.1.1"})
    mock_environ.stop()

def test_no_environ_tags():
    """
        Test No Environ tags work
    """
    test_val = 123
    mock_environ = patch.dict(os.environ, {APPTUIT_API_TOKEN: "environ_token"})
    mock_environ.start()
    client = Apptuit()
    dp1 = DataPoint("test_metric", {"host": "host2", "ip": "2.2.2.2", "test": 1}, test_val, test_val)
    dp2 = DataPoint("test_metric", {"test": 2}, test_val, test_val)
    payload = client._create_payload([dp1, dp2])
    assert_equals(len(payload), 2)
    assert_equals(payload[0]["tags"], {"host": "host2", "ip": "2.2.2.2", "test": 1})
    assert_equals(payload[1]["tags"], {"test": 2})
    registry = MetricsRegistry()
    counter = registry.counter("counter")
    counter.inc(1)
    reporter = ApptuitReporter(registry=registry, tags={"host": "reporter", "ip": "2.2.2.2"})
    payload = reporter.client._create_payload(reporter._collect_data_points(reporter.registry))
    assert_equals(len(payload), 1)
    assert_equals(payload[0]["tags"], {'host': 'reporter', 'ip': '2.2.2.2'})
    mock_environ.stop()

def test_reporter_tags_take_priority():
    """
        Test that reporter tags take priority
    """
    mock_environ = patch.dict(os.environ, {APPTUIT_API_TOKEN: "environ_token",
                                           APPTUIT_PY_TAGS: 'host: environ, ip: 1.1.1.1'})
    mock_environ.start()
    registry = MetricsRegistry()
    counter = registry.counter("counter")
    counter.inc(1)
    reporter = ApptuitReporter(registry=registry, tags={"host": "reporter", "ip": "2.2.2.2"})
    payload = reporter.client._create_payload(reporter._collect_data_points(reporter.registry))
    assert_equals(len(payload), 1)
    assert_equals(payload[0]["tags"], {'host': 'reporter', 'ip': '2.2.2.2'})
    reporter = ApptuitReporter(registry=registry)
    payload = reporter.client._create_payload(reporter._collect_data_points(reporter.registry))
    assert_equals(len(payload), 1)
    assert_equals(payload[0]["tags"], {"host": "environ", "ip": "1.1.1.1"})
    mock_environ.stop()
