'''
    NAC Service Portal
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
import re


def normalize_mac(input_string):
    try:
        input_string = input_string.replace(':', '')
        input_string = input_string.replace('-', '')
        input_string = input_string.replace(' ', '')
        input_string = input_string.lower()
    except(AttributeError):
        raise MacAddressNotValid('input is not a string type object')
    is_valid_normalized_mac(input_string)
    return input_string


def is_valid_normalized_mac(input_string):
    if len(input_string) != 12:
        raise MacAddressNotValid('input size is invalid')
    if re.search(r'[a-f0-9]{12}', input_string) is None:
        raise MacAddressNotValid('invalid characters')
    return True


class MacAddressNotValid(Exception):
    pass
