import pytest

from helper.mac import normalize_mac, is_valid_normalized_mac, MacAddressNotValid


@pytest.mark.parametrize('input_data, expected', [
    ('001122334455', '001122334455'),
    (' 001122334455 ', '001122334455'),
    ('00:00:00:00:00:00', '000000000000'),
    ('AA:bb:Cc:ee:Ff:00', 'aabbcceeff00'),
    ('01-02-03-04-05-06', '010203040506')
])
def test_normalize_mac(input_data, expected):
    assert normalize_mac(input_data) == expected


@pytest.mark.parametrize('input_data, expected', [
    (0.0, 'invalid input type'),
    ('ii1122334455', 'invalid characters'),
])
def test_normalize_mac_error(input_data, expected):
    with pytest.raises(MacAddressNotValid) as error_info:
        normalize_mac(input_data)
        assert error_info == expected


@pytest.mark.parametrize('input_data, expected', [
    ('00112233445566', 'invalid size'),
    ('ii1122334455', 'invalid characters')
])
def test_is_valid_normalized_mac_false(input_data, expected):
    with pytest.raises(MacAddressNotValid) as error_info:
        is_valid_normalized_mac(input_data)
        assert error_info == expected


def test_is_valid_nomalized_mac_true():
    assert is_valid_normalized_mac('001122334455')
