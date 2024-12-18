'''
    NSSP
    Copyright (C) 2024 Universitaetsklinikum Bonn AoeR

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
import logging
import json
from pathlib import Path
from configparser import ConfigParser


class ConfigFileNotFound(Exception):

    def __init__(self, file_path):
        super().__init__('Config file not found: {}'.format(file_path))


def get_config_from_file(file_path):
    logging.debug('configuration file: {}'.format(file_path))
    file_path = Path(file_path)
    if not file_path.exists():
        raise ConfigFileNotFound(file_path)
    config = ConfigParser()
    config.read(file_path)
    return config


def get_config_from_json(file_path):
    logging.debug('mapping file: {}'.format(file_path))
    file_path = Path(file_path)
    if not file_path.exists():
        raise ConfigFileNotFound(file_path)

    with open(file_path, 'r') as file:
        json_config = json.load(file)
    return json_config
