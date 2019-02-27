import pytest
from encoders.base import encode, describe
from encoders.jvm import Encoder, EncoderConfigException, \
    SettingConfigException, \
    SettingRuntimeException

"""
Describe helper
"""

config_base = {'name': 'jvm'}


def test_describe():
    config = {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1},
                           'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}}
    descriptor = describe(Encoder, config, ['-XX:MaxHeapSize=3072m',
                                            '-XX:GCTimeRatio=15'])
    assert descriptor == {
        'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'value': 3, 'type': 'range', 'unit': 'GiB'},
        'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'value': 15, 'type': 'range', 'unit': ''}}


def test_describe_one_setting():
    config = {'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}}
    descriptor = describe(Encoder, config, ['-XX:GCTimeRatio=15'])
    assert descriptor == {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'value': 15, 'type': 'range', 'unit': ''}}


def test_describe_one_setting_defaults():
    config = {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1},
                           'GCTimeRatio': None}}
    descriptor = describe(Encoder, config, ['-XX:MaxHeapSize=3072m',
                                            '-XX:GCTimeRatio=15'])
    assert descriptor == {
        'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'value': 3, 'type': 'range', 'unit': 'GiB'},
        'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'value': 15, 'type': 'range', 'unit': ''}}


def test_describe_no_current_value_with_default():
    config = {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'default': 3},
                           'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'default': 15}}}
    descriptor = describe(Encoder, config, [])
    assert descriptor == {
        'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'default': 3, 'value': 3, 'type': 'range', 'unit': 'GiB'},
        'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'default': 15, 'value': 15, 'type': 'range', 'unit': ''}}


def test_describe_unsupported_settings_provided():
    config = {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1},
                           'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}}
    descriptor = describe(Encoder, config, ['java', '-server',

                                            '-XX:MaxHeapSize=5120m',
                                            '-XX:GCTimeRatio=50',

                                            '-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar'])
    assert descriptor == {
        'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'value': 5, 'type': 'range', 'unit': 'GiB'},
        'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'value': 50, 'type': 'range', 'unit': ''}}


def test_describe_no_config_provided():
    assert describe(Encoder, None, ['-XX:MaxHeapSize=1024m']) == {}


def test_describe_no_current_value_without_default():
    with pytest.raises(SettingRuntimeException):
        describe(Encoder, {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}}, [])

    with pytest.raises(SettingRuntimeException):
        describe(Encoder, {'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}}, [])


def test_describe_wrong_value_format():
    with pytest.raises(SettingRuntimeException):
        describe(Encoder, {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}},
                 ['-XX:MaxHeapSize=5.2g'])

    with pytest.raises(SettingRuntimeException):
        describe(Encoder, {'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}},
                 ['-XX:GCTimeRatio=None'])


def test_describe_multiple_settings_provided():
    with pytest.raises(SettingRuntimeException):
        describe(Encoder, {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}},
                 ['-XX:MaxHeapSize=5120m', '-XX:MaxHeapSize=6144m'])

    with pytest.raises(SettingRuntimeException):
        describe(Encoder, {'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}},
                 ['-XX:GCTimeRatio=50', '-XX:GCTimeRatio=60'])


def test_describe_wrong_config_type_provided():
    with pytest.raises(EncoderConfigException):
        describe(Encoder, 'settings', ['-XX:MaxHeapSize=1024m'])


def test_describe_unsupported_setting_requested():
    with pytest.raises(EncoderConfigException):
        describe(Encoder, {'settings': {'MortgageAPR': {}}}, [])


"""
Encode helper
"""


def test_encode():
    encoded, _ = encode(Encoder, {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1},
                                               'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}},
                        {'MaxHeapSize': 4,
                         'GCTimeRatio': 59})
    assert sorted(encoded) == sorted(['-XX:MaxHeapSize=4096m',
                                      '-XX:GCTimeRatio=59'])


def test_encode_one_setting():
    encoded, _ = encode(Encoder, {'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}},
                        {'GCTimeRatio': 59})
    assert sorted(encoded) == sorted(['-XX:GCTimeRatio=59'])


def test_encode_one_setting_defaults():
    encoded, _ = encode(Encoder, {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1},
                                               'GCTimeRatio': None}},
                        {'MaxHeapSize': 4,
                         'GCTimeRatio': 59})
    assert sorted(encoded) == sorted(['-XX:MaxHeapSize=4096m',
                                      '-XX:GCTimeRatio=59'])


def test_encode_before_after_persist():
    encoded, _ = encode(Encoder, {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}},
                                  'before': ['java', '-server'],
                                  'after': ['-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar']},
                        {'MaxHeapSize': 4})
    assert encoded == ['java', '-server',
                       '-XX:MaxHeapSize=4096m',
                       '-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar']


def test_encode_value_conversion():
    encoded, _ = encode(Encoder, {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': .125}}},
                        {'MaxHeapSize': 1.625})
    assert encoded == ['-XX:MaxHeapSize=1664m']


def test_encode_no_values_provided():
    with pytest.raises(SettingRuntimeException):
        encode(Encoder, {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}},
               {})

    with pytest.raises(SettingRuntimeException):
        encode(Encoder, {'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}},
               {})


def test_encode_invalid_type_value_provided():
    with pytest.raises(SettingRuntimeException):
        encode(Encoder, {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}},
               {'MaxHeapSize': '1'})


def test_encode_setting_wrong_configuration_type():
    with pytest.raises(SettingConfigException):
        encode(Encoder, {'settings': {'MaxHeapSize': 5}}, {'MaxHeapSize': 2})


def test_encode_setting_unsupported_option():
    with pytest.raises(SettingConfigException):
        encode(Encoder, {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'magic_wand': True}}},
               {'MaxHeapSize': 2})


def test_encode_range_setting_value_validation():
    with pytest.raises(SettingConfigException):
        encode(Encoder, {'settings': {'MaxHeapSize': {'min': None, 'max': 6, 'step': 1}}},
               {'MaxHeapSize': 2})

    with pytest.raises(SettingConfigException):
        encode(Encoder, {'settings': {'MaxHeapSize': {'min': 1, 'step': 1}}},
               {'MaxHeapSize': 2})

    with pytest.raises(SettingConfigException):
        encode(Encoder, {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': None}}},
               {'MaxHeapSize': 2})

    with pytest.raises(SettingConfigException):
        encode(Encoder, {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 0}}},
               {'MaxHeapSize': 2})

    with pytest.raises(SettingConfigException):
        encode(Encoder, {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': -1}}},
               {'MaxHeapSize': 6})

    with pytest.raises(SettingConfigException):
        encode(Encoder, {'settings': {'MaxHeapSize': {'min': 6, 'max': 1, 'step': 1}}},
               {'MaxHeapSize': 2})

    with pytest.raises(SettingConfigException):
        encode(Encoder, {'settings': {'GCTimeRatio': {'min': 10, 'max': 90, 'step': 9}}},
               {'GCTimeRatio': 10})

    with pytest.raises(SettingRuntimeException):
        encode(Encoder, {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}},
               {'MaxHeapSize': 2.5})

    with pytest.raises(SettingRuntimeException):
        encode(Encoder, {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}},
               {'MaxHeapSize': 0})

    with pytest.raises(SettingRuntimeException):
        encode(Encoder, {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}},
               {'MaxHeapSize': 7})
