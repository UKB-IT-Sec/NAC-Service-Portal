from helper.filesystem import get_src_directory, get_config_directory, get_resources_directory, get_existing_path


def test_get_src_directory():
    assert (get_src_directory() / 'manage.py').exists()


def test_get_config_directory():
    assert (get_config_directory() / 'export.cnf').exists()


def test_get_resources_directory():
    assert (get_resources_directory() / 'appl-NAC.schema').exists()


def test_get_existing_path():
    path = str(get_src_directory() / 'manage.py')
    assert (get_existing_path(path)) is not None
