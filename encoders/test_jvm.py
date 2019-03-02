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
                           'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}, **config_base}
    descriptor = describe(config, ['-XX:MaxHeapSize=3072m',
                                   '-XX:GCTimeRatio=15'])
    assert descriptor == {
        'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'value': 3, 'type': 'range', 'unit': 'GiB'},
        'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'value': 15, 'type': 'range', 'unit': ''}}


def test_describe_one_setting():
    config = {'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}, **config_base}
    descriptor = describe(config, ['-XX:GCTimeRatio=15'])
    assert descriptor == {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'value': 15, 'type': 'range', 'unit': ''}}


def test_describe_boolean_setting():
    config = {'settings': {'AlwaysPreTouch': None}, **config_base}
    descriptor = describe(config, ['-XX:AlwaysPreTouch'])
    assert descriptor == {'AlwaysPreTouch': {'min': 0, 'max': 1, 'step': 1, 'default': 0, 'value': 1,
                                             'type': 'range', 'unit': ''}}
    descriptor = describe(config, ['-XX:+AlwaysPreTouch'])
    assert descriptor == {'AlwaysPreTouch': {'min': 0, 'max': 1, 'step': 1, 'default': 0, 'value': 1,
                                             'type': 'range', 'unit': ''}}
    descriptor = describe(config, ['-XX:-AlwaysPreTouch'])
    assert descriptor == {'AlwaysPreTouch': {'min': 0, 'max': 1, 'step': 1, 'default': 0, 'value': 0,
                                             'type': 'range', 'unit': ''}}


def test_describe_one_setting_defaults():
    config = {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1},
                           'GCTimeRatio': None}, **config_base}
    descriptor = describe(config, ['-XX:MaxHeapSize=3072m',
                                   '-XX:GCTimeRatio=15'])
    assert descriptor == {
        'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'value': 3, 'type': 'range', 'unit': 'GiB'},
        'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'value': 15, 'type': 'range', 'unit': ''}}


def test_describe_no_current_value_with_default():
    config = {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'default': 3},
                           'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'default': 15}}, **config_base}
    descriptor = describe(config, [])
    assert descriptor == {
        'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'default': 3, 'value': 3, 'type': 'range', 'unit': 'GiB'},
        'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'default': 15, 'value': 15, 'type': 'range', 'unit': ''}}


def test_describe_unsupported_options_provided():
    config = {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1},
                           'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}, **config_base}
    descriptor = describe(config, ['java', '-server',

                                   '-XX:MaxHeapSize=5120m',
                                   '-XX:GCTimeRatio=50',

                                   '-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar'])
    assert descriptor == {
        'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'value': 5, 'type': 'range', 'unit': 'GiB'},
        'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'value': 50, 'type': 'range', 'unit': ''}}


def test_describe_multiple_option_formats_provided():
    config = {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}, **config_base}
    with pytest.raises(SettingRuntimeException):
        describe(config, ['-XX:MaxHeapSize=5120m', '-Xmx4096m'])


def test_describe_no_config_provided():
    with pytest.raises(EncoderConfigException):
        describe(None, ['-XX:MaxHeapSize=1024m'])


def test_describe_no_settings_provided():
    assert describe(config_base, ['-XX:MaxHeapSize=1024m']) == {}


def test_describe_no_current_value_without_default():
    with pytest.raises(SettingRuntimeException):
        describe({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}, **config_base}, [])

    with pytest.raises(SettingRuntimeException):
        describe({'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}, **config_base}, [])


def test_describe_wrong_value_format():
    with pytest.raises(SettingRuntimeException):
        describe({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}, **config_base},
                 ['-XX:MaxHeapSize=5.2g'])

    with pytest.raises(SettingRuntimeException):
        describe({'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}, **config_base},
                 ['-XX:GCTimeRatio=None'])


def test_describe_multiple_settings_provided():
    with pytest.raises(SettingRuntimeException):
        describe({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}, **config_base},
                 ['-XX:MaxHeapSize=5120m', '-XX:MaxHeapSize=6144m'])

    with pytest.raises(SettingRuntimeException):
        describe({'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}, **config_base},
                 ['-XX:GCTimeRatio=50', '-XX:GCTimeRatio=60'])


def test_describe_wrong_config_type_provided():
    with pytest.raises(EncoderConfigException):
        describe('settings', ['-XX:MaxHeapSize=1024m'])


def test_describe_unsupported_setting_requested():
    with pytest.raises(EncoderConfigException):
        describe({'settings': {'MortgageAPR': {}}, **config_base}, [])


"""
Encode helper
"""


def test_encode():
    encoded, _ = encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1},
                                      'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}},
                         'expected_type': 'list', **config_base},
                        {'MaxHeapSize': {'value': 4},
                         'GCTimeRatio': {'value': 59}})
    assert sorted(encoded) == sorted(['-XX:MaxHeapSize=4096m',
                                      '-XX:GCTimeRatio=59'])


def test_encode_one_setting():
    encoded, _ = encode({'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}},
                         'expected_type': 'list', **config_base},
                        {'GCTimeRatio': {'value': 59}})
    assert sorted(encoded) == sorted(['-XX:GCTimeRatio=59'])


def test_encode_one_setting_defaults():
    encoded, _ = encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1},
                                      'GCTimeRatio': None},
                         'expected_type': 'list', **config_base},
                        {'MaxHeapSize': {'value': 4},
                         'GCTimeRatio': {'value': 59}})
    assert sorted(encoded) == sorted(['-XX:MaxHeapSize=4096m',
                                      '-XX:GCTimeRatio=59'])


def test_encode_before_after_persist():
    encoded, _ = encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}},
                         'before': ['java', '-server'],
                         'after': ['-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar'],
                         'expected_type': 'list', **config_base},
                        {'MaxHeapSize': {'value': 4}})
    assert encoded == ['java', '-server',
                       '-XX:MaxHeapSize=4096m',
                       '-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar']


def test_encode_expected_type_from_config():
    encoded, _ = encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}},
                         'before': ['java', '-server'],
                         'after': ['-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar'],
                         'expected_type': 'str', **config_base},
                        {'MaxHeapSize': {'value': 4}})
    assert encoded == 'java -server -XX:MaxHeapSize=4096m -javaagent:/tmp/newrelic/newrelic.jar -jar /app.jar'


def test_encode_expected_type_string():
    encoded, _ = encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}},
                         'before': ['java', '-server'],
                         'after': ['-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar'], **config_base},
                        {'MaxHeapSize': {'value': 4}},
                        expected_type='str')
    assert encoded == 'java -server -XX:MaxHeapSize=4096m -javaagent:/tmp/newrelic/newrelic.jar -jar /app.jar'


def test_encode_expected_type_list():
    encoded, _ = encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}},
                         'before': ['java', '-server'],
                         'after': ['-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar'], **config_base},
                        {'MaxHeapSize': {'value': 4}},
                        expected_type='list')
    assert encoded == ['java', '-server',
                       '-XX:MaxHeapSize=4096m', '-javaagent:/tmp/newrelic/newrelic.jar',
                       '-jar', '/app.jar']


def test_encode_default_expected_type_string():
    encoded, _ = encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}},
                         'before': ['java', '-server'],
                         'after': ['-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar'], **config_base},
                        {'MaxHeapSize': {'value': 4}})
    assert encoded == 'java -server -XX:MaxHeapSize=4096m -javaagent:/tmp/newrelic/newrelic.jar -jar /app.jar'


def test_encode_expected_type_provided_in_encode_and_config():
    with pytest.raises(EncoderConfigException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}},
                'before': ['java', '-server'],
                'after': ['-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar'],
                'expected_type': 'str', **config_base},
               {'MaxHeapSize': {'value': 4}},
               expected_type='list')


def test_encode_unsupported_expected_type():
    with pytest.raises(EncoderConfigException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}},
                'before': ['java', '-server'],
                'after': ['-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar'], **config_base},
               {'MaxHeapSize': {'value': 4}},
               expected_type=dict)


def test_encode_value_conversion():
    encoded, _ = encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': .125}},
                         'expected_type': 'list', **config_base},
                        {'MaxHeapSize': {'value': 1.625}})
    assert encoded == ['-XX:MaxHeapSize=1664m']


def test_encode_boolean_setting():
    encoded, _ = encode({'settings': {'AlwaysPreTouch': None}, 'expected_type': 'list', **config_base},
                        {'AlwaysPreTouch': {'value': 1}})
    assert encoded == ['-XX:+AlwaysPreTouch']
    encoded, _ = encode({'settings': {'AlwaysPreTouch': None}, 'expected_type': 'list', **config_base},
                        {'AlwaysPreTouch': {'value': 0}})
    assert encoded == ['-XX:-AlwaysPreTouch']


def test_encode_freezed_setting_reconfigure():
    with pytest.raises(SettingConfigException):
        encode({'settings': {'AlwaysPreTouch': {'max': 2}}, **config_base},
               {'AlwaysPreTouch': {'value': 2}})


def test_encode_no_values_provided():
    with pytest.raises(SettingRuntimeException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}, **config_base},
               {})

    with pytest.raises(SettingRuntimeException):
        encode({'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}, **config_base},
               {})


def test_encode_invalid_type_value_provided():
    with pytest.raises(SettingRuntimeException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}, **config_base},
               {'MaxHeapSize': {'value': '1'}})


def test_encode_setting_wrong_configuration_type():
    with pytest.raises(SettingConfigException):
        encode({'settings': {'MaxHeapSize': 5}, **config_base}, {'MaxHeapSize': {'value': 2}})


def test_encode_setting_unsupported_option():
    with pytest.raises(SettingConfigException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'magic_wand': True}}, **config_base},
               {'MaxHeapSize': {'value': 2}})


def test_encode_range_setting_value_validation():
    with pytest.raises(SettingConfigException):
        encode({'settings': {'MaxHeapSize': {'min': None, 'max': 6, 'step': 1}}, **config_base},
               {'MaxHeapSize': {'value': 2}})

    with pytest.raises(SettingConfigException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'step': 1}}, **config_base},
               {'MaxHeapSize': {'value': 2}})

    with pytest.raises(SettingConfigException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': None}}, **config_base},
               {'MaxHeapSize': {'value': 2}})

    with pytest.raises(SettingConfigException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 0}}, **config_base},
               {'MaxHeapSize': {'value': 2}})

    with pytest.raises(SettingConfigException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': -1}}, **config_base},
               {'MaxHeapSize': {'value': 6}})

    with pytest.raises(SettingConfigException):
        encode({'settings': {'MaxHeapSize': {'min': 6, 'max': 1, 'step': 1}}, **config_base},
               {'MaxHeapSize': {'value': 2}})

    with pytest.raises(SettingConfigException):
        encode({'settings': {'GCTimeRatio': {'min': 10, 'max': 90, 'step': 9}}, **config_base},
               {'GCTimeRatio': {'value': 10}})

    with pytest.raises(SettingRuntimeException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}, **config_base},
               {'MaxHeapSize': {'value': 2.5}})

    with pytest.raises(SettingRuntimeException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}, **config_base},
               {'MaxHeapSize': {'value': 0}})

    with pytest.raises(SettingRuntimeException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}, **config_base},
               {'MaxHeapSize': {'value': 7}})
