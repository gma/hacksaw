# $Id$
# (C) Cmed Ltd, 2004


import errno
import fcntl
import os
import sys
import time

import hacksaw.lib


class Processor(hacksaw.lib.Processor):

    LOCK_TIMEOUT = 5

    def __init__(self, config):
        hacksaw.lib.Processor.__init__(self, config)
        dirname = os.path.dirname(self.config.log_file)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    def acquire_lock(self):
        file_obj = file(self.config.log_file, "a")
        try:
            fcntl.lockf(file_obj.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError, e:
            if e.errno in (errno.EACCES, errno.EAGAIN):
                return None
            raise
        return file_obj
        
    def handle_message(self, message):
        file_obj = self.acquire_lock()
        start_time = time.time()
        while file_obj is None:
            if time.time() - start_time >= Processor.LOCK_TIMEOUT:
                raise IOError("Couldn't write to '%s' within %s seconds" %
                              (self.config.filename, Processor.LOCK_TIMEOUT))
            file_obj = self.acquire_lock()
        file_obj.write(message)
        file_obj.close()


class Config(hacksaw.lib.Config):

    LOG_FILE = 'logfile'

    def _get_log_file(self):
        return self._get_item(Config.LOG_FILE)

    log_file = property(_get_log_file)
