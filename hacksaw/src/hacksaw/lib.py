# $Id$
# (C) Cmed Ltd, 2004


import ConfigParser
import os


class ConfigError(RuntimeError):

    pass


class Config(object):

    GENERAL_SECTION = 'general'
    SPOOL_ITEM = 'spool'
    PROCESSORS_ITEM = 'processors'

    def __init__(self, filename):
        if not os.path.exists(filename):
            raise IOError, 'file not found: %s' % filename
        self.parser = ConfigParser.SafeConfigParser()
        self.parser.read(filename)

    def _get_general_item(self, item):
        try:
            return self.parser.get(Config.GENERAL_SECTION, item)
        except ConfigParser.NoSectionError, e:
            raise ConfigError, e

    def _get_spool_directory(self):
        return self._get_general_item(Config.SPOOL_ITEM)

    spool_directory = property(_get_spool_directory)

    def _get_processors(self):
        return [word.strip() for word in
                self._get_general_item(Config.PROCESSORS_ITEM).split(',')]

    processors = property(_get_processors)


