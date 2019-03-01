# noinspection PyUnresolvedReferences
import re
from abc import ABC

# noinspection PyUnresolvedReferences
from encoders.base import Encoder as BaseEncoder, RangeSetting as BaseRangeSetting, \
    EncoderConfigException, EncoderRuntimeException, \
    SettingConfigException, SettingRuntimeException, q


class IntToGbValueEncoder:

    @staticmethod
    def encode(value):
        return '{}m'.format(int(round(value * 1024)))

    @staticmethod
    def decode(data):
        val = data.lower()
        if val[-1] != 'm':
            raise ValueError('Invalid value {} to decode from megabytes to gigabytes.'.format(q(data)))
        return int(val[:-1]) / 1024


class IntToStrValueEncoder:

    @staticmethod
    def encode(value):
        return str(value)

    @staticmethod
    def decode(data):
        return int(data)


class IntToPlusMinusValueEncoder:

    @staticmethod
    def encode(value):
        return '+' if value else '-'

    @staticmethod
    def decode(data):
        if data == '+' or data == '':
            return 1
        elif data == '-':
            return 0


class RangeSetting(BaseRangeSetting):
    value_encoder = None
    formats = ('XX:{name}={value}',)
    shorthand = None
    preferred_format = 0

    def __init__(self, config):
        super().__init__(config)
        if self.value_encoder is None:
            raise NotImplementedError('You must provide value encoder for setting {} '
                                      'handled by class {}'.format(q(self.name), self.__class__.__name__))

    def check_class_defaults(self):
        super().check_class_defaults()
        if not self.formats or not isinstance(self.formats, (list, tuple, set)):
            raise NotImplementedError('Attribute `formats` in the setting class {} must be a list with at least '
                                      'one defined setting format. Found {}.'.format(self.__class__.__name__,
                                                                                     q(self.formats)))
        if (
                self.preferred_format is None
                or not isinstance(self.preferred_format, int)
                or self.preferred_format < 0
                or self.preferred_format >= len(self.formats)
        ):
            raise NotImplementedError('Attribute `preferred_format` in the setting class {} '
                                      'must be an integer in the range 0 to {}. '
                                      'Found {}.'.format(self.__class__.__name__, len(self.formats),
                                                         q(self.preferred_format)))

    def format_value(self, value, format_idx=None):
        if format_idx is None:
            idx = self.preferred_format
        else:
            idx = format_idx
        sformat = '-' + self.formats[idx]
        formatted = sformat.format(name=self.name, value=value, shorthand=self.shorthand)
        return formatted

    def get_first_format_match(self, value):
        for format_idx, _ in enumerate(self.formats):
            pattern = r'^{}$'.format(self.format_value('(.*)', format_idx))
            match = re.match(pattern, value)
            if match:
                return match
        return None

    def get_value_encoder(self):
        if callable(self.value_encoder):
            return self.value_encoder(self)
        return self.value_encoder

    def encode_option(self, value):
        """
        Encodes single primitive value into a list of primitive values (zero or more).

        :param value: Single primitive value
        :return list: List of multiple primitive values
        """
        value = self.validate_value(value)
        encoded_value = self.get_value_encoder().encode(value)
        return [self.format_value(encoded_value)]

    def filter_data(self, data):
        def predicate(option):
            return bool(self.get_first_format_match(option))

        return list(filter(predicate, data))

    def validate_data(self, data):
        if not isinstance(data, list):
            raise SettingRuntimeException('Expected list on input for RangeSetting. '
                                          'Got {} instead.'.format(q(type(data).__name__)))
        opts = self.filter_data(data)
        if len(opts) > 1:
            raise SettingRuntimeException('Received multiple values for setting {}, only one value is allowed '
                                          'on decode'.format(q(self.name)))
        if not opts and self.default is None:
            raise SettingRuntimeException('No value found to decode for setting {} and no '
                                          'default value was configured.'.format(q(self.name)))
        return opts

    def decode_option(self, data):
        """
        Decodes list of primitive values back into single primitive value

        :param data: List of multiple primitive values
        :return: Single primitive value
        """
        opts = self.validate_data(data)
        if opts:
            opt = opts[0]
            value = self.get_first_format_match(opt).groups()[0]
            try:
                return self.get_value_encoder().decode(value)
            except ValueError as e:
                raise SettingRuntimeException('Invalid value to decode for setting {}. '
                                              'Error: {}. Arg: {}'.format(q(self.name), str(e), opt))
        return self.default


class BooleanSetting(RangeSetting):
    value_encoder = IntToPlusMinusValueEncoder()
    formats = ('XX:{value}{name}',)
    min = 0
    max = 1
    step = 1
    freeze_range = 1


class HeapSizeSetting(RangeSetting, ABC):
    value_encoder = IntToGbValueEncoder()
    formats = ('XX:{name}={value}', 'X{shorthand}{value}', 'X{shorthand}:{value}')
    unit = 'GiB'
    min = .5
    step = .125


class MaxHeapSizeSetting(HeapSizeSetting):
    name = 'MaxHeapSize'
    shorthand = 'mx'


class InitialHeapSizeSetting(HeapSizeSetting):
    name = 'InitialHeapSize'
    formats = ('X{shorthand}{value}', 'X{shorthand}:{value}')
    shorthand = 'ms'


class InitialEdenHeapSizeSetting(HeapSizeSetting):
    name = 'InitialEdenHeapSize'
    formats = ('X{shorthand}{value}', 'X{shorthand}:{value}')
    shorthand = 'mn'
    min = .625 / 1024
    step = 32 / 1024


class GCTimeRatioSetting(RangeSetting):
    value_encoder = IntToStrValueEncoder()
    name = 'GCTimeRatio'
    min = 9
    max = 99
    step = 1
    relaxable = False


# Boolean settings
class CMSParallelRemarkEnabledSetting(BooleanSetting):
    name = 'CMSParallelRemarkEnabled'
    default = 0


class UseCMSInitiatingOccupancyOnlySetting(BooleanSetting):
    name = 'UseCMSInitiatingOccupancyOnly'
    default = 0


class CMSInitiatingOccupancyFractionSetting(RangeSetting):
    value_encoder = IntToStrValueEncoder
    name = 'CMSInitiatingOccupancyFraction'
    min = 50
    max = 95
    step = 1
    default = 92


class CMSScavengeBeforeRemarkSetting(BooleanSetting):
    name = 'CMSScavengeBeforeRemark'
    default = 0


class ScavengeBeforeFullGCSetting(BooleanSetting):
    name = 'ScavengeBeforeFullGC'
    default = 0


class AlwaysPreTouchSetting(BooleanSetting):
    name = 'AlwaysPreTouch'
    default = 0


class ExplicitGCInvokesConcurrentSetting(BooleanSetting):
    name = 'ExplicitGCInvokesConcurrent'
    default = 0


class ParallelRefProcEnabledSetting(BooleanSetting):
    name = 'ParallelRefProcEnabled'
    default = 0


class UseStringDeduplicationSetting(BooleanSetting):
    name = 'UseStringDeduplication'
    default = 0


class Encoder(BaseEncoder):

    def __init__(self, config):
        self.config = config
        self.settings = {}

        requested_settings = self.config.get('settings') or {}
        for name, setting in requested_settings.items():
            try:
                setting_class = globals()['{}Setting'.format(name)]
            except KeyError:
                raise EncoderConfigException('Setting "{}" is not supported in java-opts encoder.'.format(name))
            self.settings[name] = setting_class(setting)

    def describe(self):
        settings = []
        for setting in self.settings.values():
            settings.append(setting.describe())
        return dict(settings)

    def encode_multi(self, values):
        encoded = []
        values_to_encode = values.copy()

        encoded.extend(self.config.get('before', []))

        for name, setting in self.settings.items():
            encoded.extend(setting.encode_option(values_to_encode.pop(name, None)))

        encoded.extend(self.config.get('after', []))

        if values_to_encode:
            raise EncoderRuntimeException('We received settings to encode we do not support: {}'
                                          ''.format(', '.join(values_to_encode.keys())))

        return encoded

    def decode_multi(self, data):
        return {name: setting.decode_option(data)
                for name, setting in self.settings.items()}
