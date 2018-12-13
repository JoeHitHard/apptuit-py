"""
Tests on Apptuit class
"""
import os
from nose.tools import assert_equals, assert_raises
from apptuit.apptuit_client import APPTUIT_API_TOKEN, APPTUIT_PY_TAGS

from apptuit import Apptuit, DataPoint

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
    mock_environ = patch.dict(os.environ, {APPTUIT_PY_TAGS: '{"tagk1":22,"tagk2":"tagv2"}'})
    mock_environ.start()
    test_val = 123
    dp = DataPoint("metric", None, test_val, test_val)
    assert_equals(dp.tags, {"tagk1": 22, "tagk2": "tagv2"})
    dp = DataPoint("metric", {}, test_val, test_val)
    assert_equals(dp.tags, {"tagk1": 22, "tagk2": "tagv2"})
    dp = DataPoint("metric", {"tagk1": "tagv1", "tagk2": "tagv2"}, test_val, test_val)
    assert_equals(dp.tags, {"tagk1": "tagv1", "tagk2": "tagv2"})
    mock_environ.stop()

def test_tags_negative():
    """
        Test that invalid tag raises error
    """
    mock_environ = patch.dict(os.environ, {})
    mock_environ.start()
    test_val = 123
    with assert_raises(ValueError):
        DataPoint("metric", None, test_val, test_val)
    with assert_raises(ValueError):
        DataPoint("metric", {}, test_val, test_val)
    mock_environ.stop()
    mock_environ = patch.dict(os.environ, {APPTUIT_PY_TAGS: "{InvalidTags"})
    mock_environ.start()
    test_val = 123
    with assert_raises(ValueError):
        DataPoint("metric", None, test_val, test_val)
    mock_environ.stop()
