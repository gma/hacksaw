# $Id$
# (C) Cmed Ltd, 2004


import ConfigParser
import os


class ConfigError(RuntimeError):

    pass


class Config(object):

    def __init__(self, filename):
        if not os.path.exists(filename):
            raise IOError, "file not found: '%s'" % filename
        self.filename = filename
        self.parser = ConfigParser.SafeConfigParser()
        self.parser.read(filename)

    def _get_section(self):
        return self.__class__.__module__

    def _get_item(self, item):
        try:
            return self.parser.get(self._get_section(), item)
        except ConfigParser.NoSectionError, e:
            raise ConfigError, e


class GeneralConfig(Config):

    SPOOL = 'spool'
    PROCESSORS = 'processors'

    def _get_section(self):
        return 'general'

    def _get_spool_directory(self):
        return self._get_item(GeneralConfig.SPOOL)

    spool_directory = property(_get_spool_directory)

    def _get_processors(self):
        return [word.strip() for word in
                self._get_item(GeneralConfig.PROCESSORS).split(',')]

    processors = property(_get_processors)


class Processor(object):

    def __init__(self, config):
        self.config = config

    def handle_message(self, message):
        raise NotImplementedError
