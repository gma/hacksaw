# $Id$
# (C) Cmed Ltd, 2004


import hacksaw.lib


class Processor(object):

    pass


class Config(hacksaw.lib.Config):

    MESSAGE_STORE = 'messagestore'

    def _get_message_store(self):
        return self._get_item(Config.MESSAGE_STORE)

    message_store = property(_get_message_store)
