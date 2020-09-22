# noinspection PyUnresolvedReferences
import re
from abc import ABC

# noinspection PyUnresolvedReferences
from encoders.base import Encoder as BaseEncoder, RangeSetting as BaseRangeSetting, \
    EncoderConfigException, EncoderRuntimeException, \
    SettingConfigException, SettingRuntimeException, q

# valid mem units: E, P, T, G, M, K, Ei, Pi, Ti, Gi, Mi, Ki
# nb: 'm' suffix found after setting 0.7Gi
mumap = {"E":1000**6,  "P":1000**5,  "T":1000**4,  "G":1000**3,  "M":1000**2,  "K":1000, "m":1000**-1,
         "Ei":1024**6, "Pi":1024**5, "Ti":1024**4, "Gi":1024**3, "Mi":1024**2, "Ki":1024}

class IntToGbValueEncoder:

    @staticmethod
    def encode(value):
        return '{}m'.format(int(round(value * 1024)))

    @staticmethod
    def decode(data):
        data = data.strip()
        for u, m in mumap.items():
            if data.endswith(u):
                return (float(data[:-len(u)]) * m) / mumap["Gi"]

        raise ValueError('Unable to decode value {} to gigabytes.'.format(q(data)))
        # return float(s) assume to be bytes?


class IntToStrValueEncoder:

    @staticmethod
    def encode(value):
        return str(int(value))

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

    def __init__(self, config=None):
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
        index = self.preferred_format if format_idx is None else format_idx
        template = '-' + self.formats[index]
        formatted = template.format(name=self.name, value=value, shorthand=self.shorthand)
        return formatted

    def get_format_match(self, value):
        for format_idx, _ in enumerate(self.formats):
            pattern = r'^{}$'.format(self.format_value('(.*)', format_idx))
            match = re.match(pattern, value)
            if match:
                return match
        return None

    def get_value_encoder(self):
        if callable(self.value_encoder):
            return self.value_encoder()
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
            return bool(self.get_format_match(option))

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
        Decodes list of primitive values back into single primitive value.

        :param data: List of multiple primitive values
        :return: Single primitive value
        """
        opts = self.validate_data(data)
        if opts:
            opt = opts[0]
            value = self.get_format_match(opt).groups()[0]
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
    shorthand = 'ms'


class InitialEdenHeapSizeSetting(HeapSizeSetting):
    name = 'InitialEdenHeapSize'
    shorthand = 'mn'
    min = 32 / 1024
    step = 32 / 1024


class GCTimeRatioSetting(RangeSetting):
    value_encoder = IntToStrValueEncoder()
    name = 'GCTimeRatio'
    min = 9
    max = 99
    step = 1
    relaxable = False


class G1NewSizePercentSetting(RangeSetting):
    value_encoder = IntToStrValueEncoder()
    name = 'G1NewSizePercent'
    min = 0
    max = 100
    step = 1
    default = 5


class G1ReservePercentSetting(RangeSetting):
    value_encoder = IntToStrValueEncoder()
    name = 'G1ReservePercent'
    min = 0
    max = 100
    step = 1
    default = 10


class G1MixedGCLiveThresholdPercentSetting(RangeSetting):
    value_encoder = IntToStrValueEncoder()
    name = 'G1MixedGCLiveThresholdPercent'
    min = 0
    max = 100
    step = 1
    default = 65


class MaxGCPauseMillisSetting(RangeSetting):
    value_encoder = IntToStrValueEncoder()
    name = 'MaxGCPauseMillis'
    min = 1
    max = 1000
    step = 1
    default = 200


class NewRatioSetting(RangeSetting):
    value_encoder = IntToStrValueEncoder()
    name = 'NewRatio'
    min = 1
    max = 99
    step = 1
    default = 2


class SurvivorRatioSetting(RangeSetting):
    value_encoder = IntToStrValueEncoder()
    name = 'SurvivorRatio'
    min = 1
    max = 99
    step = 1
    default = 8


class TargetSurvivorRatioSetting(RangeSetting):
    value_encoder = IntToStrValueEncoder()
    name = 'TargetSurvivorRatio'
    min = 9
    max = 99
    step = 1
    default = 50


class StackShadowPagesSetting(RangeSetting):
    value_encoder = IntToStrValueEncoder()
    name = 'StackShadowPages'
    min = 0
    max = 100
    step = 1
    default = 20


class GCTypeSetting(BaseRangeSetting):
    name = 'GCType'
    type = 'enum'
    freeze_range = True
    min = 0
    max = 0
    step = 1
    supported_values = ('ParNewGC', 'G1GC', 'ParallelOldGC', 'ConcMarkSweepGC', 'SerialGC')
    values = supported_values
    disable_others = False

    def __init__(self, config=None):
        self.allowed_options.update({'values', 'disable_others'})
        super().__init__(config)
        if self.config.get('values'):
            self.values = self.config.get('values')

        if self.default is not None and self.default not in self.values:
            raise SettingConfigException(
                'Default value for setting GCType was not found in the defined list of values. '
                'Found {}. Supported: {}'.format(q(self.default), self.values))

        self.max = len(self.values) - 1

        disable_others = self.config.get('disable_others')
        if disable_others is not None:
            self.disable_others = disable_others

        self.settings = []
        for value in self.values:
            class Setting(BooleanSetting):
                name = value
                default = 0
                formats = ('XX:{value}Use{name}',)

            setting = Setting()
            self.settings.append(setting)

    def describe(self):
        name, descr = super().describe()
        descr['values'] = [*self.values]
        del descr['min']
        del descr['max']
        del descr['step']
        return name, descr

    def check_config(self):
        super().check_config()
        values = self.config.get('values')
        if values is not None:
            if not isinstance(values, (list, tuple)):
                raise SettingConfigException('Provided set of values must be a list or a tuple in setting GCType. '
                                             'Found: {}'.format(values))
            if len(values) == 0:
                raise SettingConfigException('No values has been provided for setting GCType.')
            unrecognized_values = set(values) - set(self.supported_values)
            if unrecognized_values:
                raise SettingConfigException('Provided set of values in setting GCType contains those '
                                             'it does not support: {}'.format(', '.join(unrecognized_values)))
        default = self.config.get('default')
        if default is not None and default not in self.supported_values:
            raise SettingConfigException('Provided default value in setting GCType is not allowed. '
                                         'Found {}. Supported {}.'.format(default, ', '.join(self.supported_values)))

    def validate_value(self, value):
        if value not in self.values:
            raise SettingRuntimeException('Provided value {} for encode is not '
                                          'one of the available ones: {}.'.format(q(value), ', '.join(self.values)))
        value = self.values.index(value)
        value = super().validate_value(value)
        return value

    def encode_option(self, value):
        value = self.validate_value(value)
        value_index = value
        current_value = self.values[value_index]
        encoded = []
        if self.disable_others:
            disabled_gcs = set(self.supported_values) - {current_value}
            for gc in sorted(disabled_gcs):
                encoded.append('-XX:-Use{}'.format(gc))
        encoded.append('-XX:+Use{}'.format(current_value))
        return encoded

    def validate_data(self, data):
        decoded_values = {setting.name: setting.decode_option(data) for setting in self.settings}

        if sum(decoded_values.values()) > 1:
            raise SettingRuntimeException('There is more than 1 active GC in the input data for setting GCType.')

        if not any(decoded_values.values()) and self.default is None:
            raise SettingRuntimeException('No value found to decode for setting GCType and no '
                                          'default value was configured.'.format(q(self.name)))

        return decoded_values

    def decode_option(self, data):
        decoded_values = self.validate_data(data)

        if any(decoded_values.values()):
            value = list(filter(lambda i: i[1] == 1, decoded_values.items()))[0][0]
            return value

        return self.default


# Boolean settings
class CMSParallelRemarkEnabledSetting(BooleanSetting):
    name = 'CMSParallelRemarkEnabled'
    default = 0


class UseCMSInitiatingOccupancyOnlySetting(BooleanSetting):
    name = 'UseCMSInitiatingOccupancyOnly'
    default = 0


class CMSInitiatingOccupancyFractionSetting(RangeSetting):
    value_encoder = IntToStrValueEncoder()
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


class UnlockExperimentalVMOptionsSetting(BooleanSetting):
    name = 'UnlockExperimentalVMOptions'
    default = 0


class UseCGroupMemoryLimitForHeapSetting(BooleanSetting):
    name = 'UseCGroupMemoryLimitForHeap'
    default = 0


class Encoder(BaseEncoder):

    def __init__(self, config):
        super().__init__(config)
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

    def _encode_multi(self, values):
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

    def encode_multi(self, values, expected_type=None):
        encoded = self._encode_multi(values)
        expected_type = str if expected_type is None else expected_type
        if expected_type in ('str', str):
            return ' '.join(encoded)
        if expected_type in ('list', list):
            return encoded
        raise EncoderConfigException('Unrecognized expected_type passed on encode in jvm encoder: {}. '
                                     'Supported: "list", "str"'.format(q(expected_type)))

    def _decode_multi(self, data):
        return {name: setting.decode_option(data)
                for name, setting in self.settings.items()}

    def decode_multi(self, data):
        if isinstance(data, str):
            # TODO: There might be cases with escaped spaces - this code is to be advanced.
            data = data.split(' ')
        return self._decode_multi(data)
