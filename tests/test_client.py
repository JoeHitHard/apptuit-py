"""
Tests on Apptuit class
"""
import os

from nose.tools import assert_equals, assert_raises

from apptuit import Apptuit

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch

def test_token_positive():
    """
    Test that token is working normally
    """
    mock_environ=patch.dict(os.environ,{"APPTUIT_API_TOKEN":"environ_token"})
    mock_environ.start()
    client=Apptuit()
    assert_equals(client.token,"environ_token")
    client=Apptuit(token="")
    assert_equals(client.token, "environ_token")
    client=Apptuit(token="argument_token")
    assert_equals(client.token, "argument_token")
    mock_environ.stop()

def test_token_negative():
    mock_environ = patch.dict(os.environ, {"NO_TOKEN": "environ_token"})
    mock_environ.start()
    with assert_raises(ValueError) as m:
        client = Apptuit()
    with assert_raises(ValueError) as m:
        client = Apptuit(token="")
    mock_environ.stop()




