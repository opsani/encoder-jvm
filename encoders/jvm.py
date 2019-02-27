# noinspection PyUnresolvedReferences
from encoders.base import BaseEncoder, EncoderConfigException, EncoderRuntimeException, RangeSetting,\
    SettingConfigException, SettingRuntimeException, q


class IntGbToStrPrefixMbEncoder:

    @staticmethod
    def encode(value):
        return '{}m'.format(int(round(value * 1024)))

    @staticmethod
    def decode(data):
        val = data.lower()
        if val[-1] != 'm':
            raise ValueError('Invalid value {} to decode from megabytes to gigabytes.'.format(q(data)))
        return int(val[:-1]) / 1024


class StrToIntEncoder:

    @staticmethod
    def encode(value):
        return str(value)

    @staticmethod
    def decode(data):
        return int(data)


class JavaOptionSetting(RangeSetting):
    value_encoder = None

    def __init__(self, config):
        super().__init__(config)
        if self.value_encoder is None:
            raise NotImplementedError('You must provide value encoder for setting {} '
                                      'handled by class {}'.format(q(self.name), self.__class__.__name__))

    def encode_option(self, value):
        """
        Encodes single primitive value into a list of primitive values (zero or more).

        :param value: Single primitive value
        :return list: List of multiple primitive values
        """
        value = self.validate_value(value)
        return ['-XX:{}={}'.format(self.name, self.value_encoder.encode(value))]

    def validate_data(self, data):
        found_opts = list(filter(lambda arg: arg.startswith('-XX:{}'.format(self.name)), data))
        if len(found_opts) > 1:
            raise SettingRuntimeException('Received multiple values for setting {}, only one value is allowed '
                                          'on decode'.format(q(self.name)))
        if not found_opts and self.default is None:
            raise SettingRuntimeException('No value found to decode for setting {} and no '
                                          'default value was configured.'.format(q(self.name)))
        return found_opts

    def decode_option(self, data):
        """
        Decodes list of primitive values back into single primitive value

        :param data: List of multiple primitive values
        :return: Single primitive value
        """
        opts = self.validate_data(data)
        if opts:
            opt = opts[0]
            try:
                return self.value_encoder.decode(opt.split('=', 1)[1])
            except ValueError as e:
                raise SettingRuntimeException('Invalid value to decode for setting {}. '
                                              'Error: {}. Arg: {}'.format(q(self.name), str(e), opt))
        return self.default


class MaxHeapSizeSetting(JavaOptionSetting):
    value_encoder = IntGbToStrPrefixMbEncoder()
    name = 'MaxHeapSize'
    unit = 'GiB'
    min = .5
    step = .125


class GCTimeRatioSetting(JavaOptionSetting):
    value_encoder = StrToIntEncoder()
    name = 'GCTimeRatio'
    min = 9
    max = 99
    step = 1
    can_relax = False


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
            self.settings[name] = setting_class(setting or {})

    def describe(self):
        settings = []
        for setting in self.settings.values():
            settings.append(setting.describe())
        return dict(settings)

    def encode_multi(self, values):
        ret = []
        values_to_encode = values.copy()

        ret.extend(self.config.get('before', []))

        for name, setting in self.settings.items():
            ret.extend(setting.encode_option(values_to_encode.pop(name, None)))

        ret.extend(self.config.get('after', []))

        if values_to_encode:
            raise EncoderRuntimeException('We received settings to encode we do not support {}'
                                          ''.format(list(values_to_encode.keys())))

        return ret

    def decode_multi(self, data):
        return dict((name, dict(value=setting.decode_option(data)))
                    for name, setting in self.settings.items())
