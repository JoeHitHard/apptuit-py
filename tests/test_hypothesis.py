import os

from hypothesis import strategies as st
from hypothesis import given
from string import ascii_lowercase, ascii_uppercase, digits

from nose.tools import assert_raises

from apptuit import APPTUIT_PY_TAGS, apptuit_client
from apptuit.utils import _contains_valid_chars

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch
all_characters = ascii_lowercase+ascii_uppercase+digits+"-_./"+"[]\"'?/><;:{}|/*"

@given(st.dictionaries(st.text(alphabet=all_characters, min_size=1), st.text(alphabet=all_characters, min_size=1), min_size=1 ))
def test(env_tags_value):
    env_tags_str = ""
    invalid_dict = True
    for key in env_tags_value:
        if _contains_valid_chars(key+env_tags_value[key]) and invalid_dict:
            invalid_dict = True
            continue
        env_tags_str += key + ":" + env_tags_value[key] + ","
        invalid_dict = False
    if invalid_dict:
        return
    mock_environ = patch.dict(os.environ, {APPTUIT_PY_TAGS: env_tags_str})
    mock_environ.start()
    with assert_raises(ValueError):
        apptuit_client._get_tags_from_environment()
    mock_environ.stop()

