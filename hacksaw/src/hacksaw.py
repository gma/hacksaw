# $Id$
# (C) Cmed Ltd, 2004


import ConfigParser


class Config(object):

    GENERAL_SECTION = 'general'
    SPOOL_ITEM = 'spool'

    def __init__(self, filename):
        self.parser = ConfigParser.SafeConfigParser()
        self.parser.read(filename)

    def _get_spool_directory(self):
        return self.parser.get(Config.GENERAL_SECTION, Config.SPOOL_ITEM)

    spool_directory = property(_get_spool_directory)
