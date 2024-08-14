import pytest

from helper.filesystem import get_config_directory, get_src_directory
from configparser import MissingSectionHeaderError
from helper.config import get_config_from_file, ConfigFileNotFound

CONFIG_DIR = get_config_directory()
SRC_DIR = get_src_directory()


def test_config_loaded_success():
    conf_file = CONFIG_DIR / 'export.cnf'
    configuration = get_config_from_file(conf_file)
    assert 'ldap-server' in configuration


@pytest.mark.parametrize('config_file, expected_exception, expected_message', [
    ('/none/existing/path.cnf', ConfigFileNotFound, 'Config file not found: /none/existing/path.cnf'),
    (SRC_DIR / 'requirements.txt', MissingSectionHeaderError, 'File contains no section headers.')
])
def test_config_load_failed(config_file, expected_exception, expected_message):
    with pytest.raises(expected_exception) as error_info:
        get_config_from_file(config_file)
        assert error_info == expected_message
