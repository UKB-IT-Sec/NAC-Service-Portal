from helper.filesystem import get_src_directory, get_config_directory


def test_get_src_directory():
    assert (get_src_directory() / 'manage.py').exists()


def test_get_config_directory():
    assert (get_config_directory() / 'export.cnf').exists()
