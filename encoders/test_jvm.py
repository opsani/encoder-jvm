import pytest
from encoders.base import encode as original_encode, describe as original_describe
from encoders.jvm import EncoderConfigException, \
    SettingConfigException, \
    SettingRuntimeException, GCTypeSetting

"""
Describe helper
"""

config_base = {'name': 'jvm'}


def describe(config, data):
    if isinstance(config, dict):
        config = {**config, **config_base}
    return original_describe(config, data)


def encode(config, values, expected_type=None):
    if isinstance(config, dict):
        config = {**config, **config_base}
    return original_encode(config, values, expected_type)


def test_describe_list():
    config = {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1},
                           'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}}
    descriptor = describe(config, ['-XX:MaxHeapSize=3072m',
                                   '-XX:GCTimeRatio=19'])
    assert descriptor == {
        'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'value': 3, 'type': 'range', 'unit': 'GiB'},
        'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'value': 19, 'type': 'range', 'unit': ''}}


def test_describe_string():
    config = {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1},
                           'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}}
    descriptor = describe(config, '-XX:MaxHeapSize=3072m -XX:GCTimeRatio=19')
    assert descriptor == {
        'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'value': 3, 'type': 'range', 'unit': 'GiB'},
        'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'value': 19, 'type': 'range', 'unit': ''}}


def test_describe_one_setting():
    config = {'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}}
    descriptor = describe(config, ['-XX:GCTimeRatio=19'])
    assert descriptor == {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'value': 19, 'type': 'range', 'unit': ''}}


def test_describe_boolean_setting():
    config = {'settings': {'AlwaysPreTouch': None}}
    descriptor = describe(config, ['-XX:AlwaysPreTouch'])
    assert descriptor == {'AlwaysPreTouch': {'min': 0, 'max': 1, 'step': 1, 'value': 1,
                                             'type': 'range', 'unit': ''}}
    descriptor = describe(config, ['-XX:+AlwaysPreTouch'])
    assert descriptor == {'AlwaysPreTouch': {'min': 0, 'max': 1, 'step': 1, 'value': 1,
                                             'type': 'range', 'unit': ''}}
    descriptor = describe(config, ['-XX:-AlwaysPreTouch'])
    assert descriptor == {'AlwaysPreTouch': {'min': 0, 'max': 1, 'step': 1, 'value': 0,
                                             'type': 'range', 'unit': ''}}


def test_describe_one_setting_defaults():
    config = {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1},
                           'GCTimeRatio': None}}
    descriptor = describe(config, ['-XX:MaxHeapSize=3072m',
                                   '-XX:GCTimeRatio=19'])
    assert descriptor == {
        'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'value': 3, 'type': 'range', 'unit': 'GiB'},
        'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'value': 19, 'type': 'range', 'unit': ''}}


def test_describe_no_current_value_with_default():
    config = {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'default': 3},
                           'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'default': 19}}}
    descriptor = describe(config, [])
    assert descriptor == {
        'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'value': 3, 'type': 'range', 'unit': 'GiB'},
        'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'value': 19, 'type': 'range', 'unit': ''}}


def test_describe_unsupported_options_provided():
    config = {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1},
                           'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}}
    descriptor = describe(config, ['java', '-server',

                                   '-XX:MaxHeapSize=5120m',
                                   '-XX:GCTimeRatio=50',

                                   '-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar'])
    assert descriptor == {
        'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'value': 5, 'type': 'range', 'unit': 'GiB'},
        'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'value': 50, 'type': 'range', 'unit': ''}}


def test_describe_multiple_option_formats_provided():
    config = {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}}
    with pytest.raises(SettingRuntimeException):
        describe(config, ['-XX:MaxHeapSize=5120m', '-Xmx4096m'])


def test_describe_no_config_provided():
    with pytest.raises(EncoderConfigException):
        describe(None, ['-XX:MaxHeapSize=1024m'])


def test_describe_no_settings_provided():
    assert describe(config_base, ['-XX:MaxHeapSize=1024m']) == {}


def test_describe_no_current_value_without_default():
    with pytest.raises(SettingRuntimeException):
        describe({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}}, [])

    with pytest.raises(SettingRuntimeException):
        describe({'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}}, [])


def test_describe_wrong_value_format():
    with pytest.raises(SettingRuntimeException):
        describe({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}},
                 ['-XX:MaxHeapSize=5.2g'])

    with pytest.raises(SettingRuntimeException):
        describe({'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}},
                 ['-XX:GCTimeRatio=None'])


def test_describe_multiple_settings_provided():
    with pytest.raises(SettingRuntimeException):
        describe({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}},
                 ['-XX:MaxHeapSize=5120m', '-XX:MaxHeapSize=6144m'])

    with pytest.raises(SettingRuntimeException):
        describe({'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}},
                 ['-XX:GCTimeRatio=50', '-XX:GCTimeRatio=60'])


def test_describe_wrong_config_type_provided():
    with pytest.raises(EncoderConfigException):
        describe('settings', ['-XX:MaxHeapSize=1024m'])


def test_describe_unsupported_setting_requested():
    with pytest.raises(EncoderConfigException):
        describe({'settings': {'MortgageAPR': {}}}, [])


"""
Encode helper
"""


def test_encode():
    encoded, _ = encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1},
                                      'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}},
                         'expected_type': 'list'},
                        {'MaxHeapSize': {'value': 4},
                         'GCTimeRatio': {'value': 59}})
    assert sorted(encoded) == sorted(['-XX:MaxHeapSize=4096m',
                                      '-XX:GCTimeRatio=59'])


def test_encode_one_setting():
    encoded, _ = encode({'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}},
                         'expected_type': 'list'},
                        {'GCTimeRatio': {'value': 59}})
    assert sorted(encoded) == sorted(['-XX:GCTimeRatio=59'])


def test_encode_one_setting_defaults():
    encoded, _ = encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1},
                                      'GCTimeRatio': None},
                         'expected_type': 'list'},
                        {'MaxHeapSize': {'value': 4},
                         'GCTimeRatio': {'value': 59}})
    assert sorted(encoded) == sorted(['-XX:MaxHeapSize=4096m',
                                      '-XX:GCTimeRatio=59'])


def test_encode_before_after_persist():
    encoded, _ = encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}},
                         'before': ['java', '-server'],
                         'after': ['-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar'],
                         'expected_type': 'list'},
                        {'MaxHeapSize': {'value': 4}})
    assert encoded == ['java', '-server',
                       '-XX:MaxHeapSize=4096m',
                       '-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar']


def test_encode_expected_type_from_config():
    encoded, _ = encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}},
                         'before': ['java', '-server'],
                         'after': ['-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar'],
                         'expected_type': 'str'},
                        {'MaxHeapSize': {'value': 4}})
    assert encoded == 'java -server -XX:MaxHeapSize=4096m -javaagent:/tmp/newrelic/newrelic.jar -jar /app.jar'


def test_encode_expected_type_string():
    encoded, _ = encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}},
                         'before': ['java', '-server'],
                         'after': ['-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar']},
                        {'MaxHeapSize': {'value': 4}},
                        expected_type='str')
    assert encoded == 'java -server -XX:MaxHeapSize=4096m -javaagent:/tmp/newrelic/newrelic.jar -jar /app.jar'


def test_encode_expected_type_list():
    encoded, _ = encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}},
                         'before': ['java', '-server'],
                         'after': ['-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar']},
                        {'MaxHeapSize': {'value': 4}},
                        expected_type='list')
    assert encoded == ['java', '-server',
                       '-XX:MaxHeapSize=4096m', '-javaagent:/tmp/newrelic/newrelic.jar',
                       '-jar', '/app.jar']
    encoded, _ = encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}},
                         'before': ['java', '-server'],
                         'after': ['-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar']},
                        {'MaxHeapSize': {'value': 4}},
                        expected_type=list)
    assert encoded == ['java', '-server',
                       '-XX:MaxHeapSize=4096m', '-javaagent:/tmp/newrelic/newrelic.jar',
                       '-jar', '/app.jar']


def test_encode_default_expected_type_string():
    encoded, _ = encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}},
                         'before': ['java', '-server'],
                         'after': ['-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar']},
                        {'MaxHeapSize': {'value': 4}})
    assert encoded == 'java -server -XX:MaxHeapSize=4096m -javaagent:/tmp/newrelic/newrelic.jar -jar /app.jar'


def test_encode_expected_type_provided_in_encode_and_config():
    with pytest.raises(EncoderConfigException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}},
                'before': ['java', '-server'],
                'after': ['-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar'],
                'expected_type': 'str'},
               {'MaxHeapSize': {'value': 4}},
               expected_type='list')


def test_encode_unsupported_expected_type():
    with pytest.raises(EncoderConfigException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}},
                'before': ['java', '-server'],
                'after': ['-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar']},
               {'MaxHeapSize': {'value': 4}},
               expected_type=dict)


def test_encode_value_conversion():
    encoded, _ = encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': .125}},
                         'expected_type': 'list'},
                        {'MaxHeapSize': {'value': 1.625}})
    assert encoded == ['-XX:MaxHeapSize=1664m']


def test_encode_boolean_setting():
    encoded, _ = encode({'settings': {'AlwaysPreTouch': None}, 'expected_type': 'list'},
                        {'AlwaysPreTouch': {'value': 1}})
    assert encoded == ['-XX:+AlwaysPreTouch']
    encoded, _ = encode({'settings': {'AlwaysPreTouch': None}, 'expected_type': 'list'},
                        {'AlwaysPreTouch': {'value': 0}})
    assert encoded == ['-XX:-AlwaysPreTouch']


def test_encode_freezed_setting_reconfigure():
    with pytest.raises(SettingConfigException):
        encode({'settings': {'AlwaysPreTouch': {'max': 2}}},
               {'AlwaysPreTouch': {'value': 2}})


def test_encode_no_values_provided():
    with pytest.raises(SettingRuntimeException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}},
               {})

    with pytest.raises(SettingRuntimeException):
        encode({'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}},
               {})


def test_encode_invalid_type_value_provided():
    with pytest.raises(SettingRuntimeException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}},
               {'MaxHeapSize': {'value': '1'}})


def test_encode_setting_wrong_configuration_type():
    with pytest.raises(SettingConfigException):
        encode({'settings': {'MaxHeapSize': 5}}, {'MaxHeapSize': {'value': 2}})


def test_encode_setting_unsupported_option():
    with pytest.raises(SettingConfigException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'magic_wand': True}}},
               {'MaxHeapSize': {'value': 2}})


def test_encode_range_setting_value_validation():
    with pytest.raises(SettingConfigException):
        encode({'settings': {'MaxHeapSize': {'min': None, 'max': 6, 'step': 1}}},
               {'MaxHeapSize': {'value': 2}})

    with pytest.raises(SettingConfigException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'step': 1}}},
               {'MaxHeapSize': {'value': 2}})

    with pytest.raises(SettingConfigException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': None}}},
               {'MaxHeapSize': {'value': 2}})

    with pytest.raises(SettingConfigException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 0}}},
               {'MaxHeapSize': {'value': 2}})

    with pytest.raises(SettingConfigException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': -1}}},
               {'MaxHeapSize': {'value': 6}})

    with pytest.raises(SettingConfigException):
        encode({'settings': {'MaxHeapSize': {'min': 6, 'max': 1, 'step': 1}}},
               {'MaxHeapSize': {'value': 2}})

    with pytest.raises(SettingConfigException):
        encode({'settings': {'GCTimeRatio': {'min': 10, 'max': 90, 'step': 9}}},
               {'GCTimeRatio': {'value': 10}})

    with pytest.raises(SettingRuntimeException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}},
               {'MaxHeapSize': {'value': 2.5}})

    with pytest.raises(SettingRuntimeException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}},
               {'MaxHeapSize': {'value': 0}})

    with pytest.raises(SettingRuntimeException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}},
               {'MaxHeapSize': {'value': 7}})


# GC Type
def test_describe_gc_type():
    selected_gcs = ['ParNewGC', 'G1GC', 'ParallelOldGC']
    supported_gcs = set(GCTypeSetting.supported_values)
    template = '-XX:{}Use{}'

    # Test all the available GCs with and without disabling other types
    for disable_others in (True, False):
        for current_gc in selected_gcs:
            input_data = []
            if disable_others:
                disabled_gcs = supported_gcs - set(selected_gcs)
                for gc in disabled_gcs:
                    input_data.append(template.format('-', gc))
            input_data.append(template.format('+', current_gc))
            config = {'settings': {'GCType': {'values': selected_gcs,
                                              'disable_others': disable_others}}}
            descriptor = describe(config, input_data)
            assert descriptor == {'GCType': {'value': current_gc, 'values': selected_gcs, 'type': 'enum', 'unit': ''}}


def test_describe_gc_type_default_value_provided():
    selected_gcs = ['G1GC', 'ConcMarkSweepGC', 'ParNewGC', 'ParallelOldGC']
    # Test default value
    config = {'settings': {'GCType': {'values': selected_gcs, 'default': 'ParNewGC'}}}
    descriptor = describe(config, [])
    assert descriptor == {'GCType': {'value': 'ParNewGC', 'values': selected_gcs, 'type': 'enum', 'unit': ''}}


def test_describe_gc_type_no_default_value_provided():
    config = {'settings': {'GCType': {'values': ['G1GC', 'ConcMarkSweepGC', 'ParNewGC', 'ParallelOldGC']}}}
    with pytest.raises(SettingRuntimeException):
        describe(config, [])


def test_describe_gc_type_wrong_default_value_provided():
    config = {'settings': {'GCType': {'values': ['G1GC', 'ConcMarkSweepGC', 'ParNewGC', 'ParallelOldGC'],
                                      'default': 'CerealGC'}}}
    with pytest.raises(SettingConfigException):
        describe(config, [])


def test_describe_gc_type_multiple_enabled():
    config = {'settings': {'GCType': {'values': ['G1GC', 'ConcMarkSweepGC', 'ParNewGC', 'ParallelOldGC']}}}
    with pytest.raises(SettingRuntimeException):
        describe(config, ['-XX:+UseParNewGC', '-XX:+UseConcMarkSweepGC'])


def test_describe_gc_type_no_values_provided():
    with pytest.raises(SettingConfigException):
        describe({'settings': {'GCType': {'values': []}}}, [])


def test_describe_gc_type_wrong_type_value_set_provided():
    with pytest.raises(SettingConfigException):
        describe({'settings': {'GCType': {'values': 'hello, world!'}}}, [])


def test_describe_gc_type_unsupported_value_provided():
    with pytest.raises(SettingConfigException):
        describe({'settings': {'GCType': {'values': ['G1GC', 'ConcMarkSweepGC', 'ParNewGC', 'CerealGC']}}}, [])


def test_encode_gc_type():
    selected_gcs = ('ParNewGC', 'G1GC', 'ParallelOldGC')
    supported_gcs = set(GCTypeSetting.supported_values)
    template = '-XX:{}Use{}'

    # Test all the available GCs with and without disabling other types
    for disable_others in (True, False):
        for current_gc in selected_gcs:
            config = {'settings': {'GCType': {'values': selected_gcs, 'disable_others': disable_others}}}
            expected = []
            if disable_others:
                disabled_gcs = supported_gcs - {current_gc}
                for gc in sorted(disabled_gcs):
                    expected.append(template.format('-', gc))
            expected.append(template.format('+', current_gc))
            encoded, _ = encode(config, {'GCType': {'value': current_gc}}, list)
            assert encoded == expected


def test_encode_gc_type_unsupported_value_provided():
    selected_gcs = ('ParNewGC', 'G1GC', 'ParallelOldGC')
    with pytest.raises(SettingRuntimeException):
        encode({'settings': {'GCType': {'values': selected_gcs}}}, {'GCType': {'value': 'CerealGC'}}, list)
